"""This module provides interface for interacting with S3 data lake."""
import logging
import json
from typing import Generator, Dict, List, Tuple, Union
from dataclasses import dataclass
from io import StringIO, BytesIO
from itertools import chain
import pandas as pd
import boto3
import botocore
import hydro_serving_grpc as hs
from src.utils import DTYPE_CONVERSIONS, VALUE_CONVERSIONS
from src.clients import ClientFactory

logger = logging.getLogger('main')


@dataclass
class ColumnDescription:
    # pylint: disable=missing-class-docstring
    name: str
    dtype: str
    htype: str
    shape: Tuple[int]


@dataclass
class SchemaDescription:
    # pylint: disable=missing-class-docstring
    inputs: List[ColumnDescription]
    outputs: List[ColumnDescription]


@dataclass
class Column:
    # pylint: disable=missing-class-docstring
    description: ColumnDescription
    data: str


@dataclass
class Metadata:
    # pylint: disable=missing-class-docstring
    event_id: str
    inference_time: str


class Record:
    """
    Represents an object on S3 bucket and available operations on top of it.
    """
    def __init__(
            self,
            bucket: str,
            key: str,
            session: Union[boto3.Session, botocore.session.Session, None] = None,
    ) -> 'Record':
        self.bucket = bucket
        self.key = key

        self._session = session or boto3.Session()
        self._s3_client = ClientFactory.get_client('s3', self._session)

    @classmethod
    def from_event_record(
            cls,
            event_record: dict, 
            session: Union[boto3.Session, botocore.session.Session, None] = None
    ) -> 'Record':
        return cls(
            event_record['s3']['bucket']['name'],
            event_record['s3']['object']['key'],
            session
        )

    def read(self) -> Generator[Dict, None, None]:
        """Iterate by lines on the remote object."""
        obj = self._s3_client.get_object(Bucket=self.bucket, Key=self.key)
        for line in obj['Body'].iter_lines():
            yield line


class Contract:
    """Represents a contract for the model, inferred from file."""
    def __init__(
            self,
            capture_record: Record,                     # Should be jsonl file
            train_record: Union[Record, None] = None,   # Should be csv file
            session: Union[boto3.Session, botocore.session.Session, None] = None
    ) -> 'Contract':
        self._session = session or boto3.Session()
        self._s3_client = ClientFactory.get_client('s3', self._session)

        self.capture_record = capture_record
        self.train_record = train_record
        self.schema = self._parse_schema()
        if self.train_record:
            self._update_headers()

    def _parse_schema(self) -> SchemaDescription:
        """
        Infer inputs and outputs of the model based on the downloaded
        file contents.
        """
        data = json.loads(next(self.capture_record.read()))
        inputs = data['captureData']['endpointInput']
        outputs = data['captureData']['endpointOutput']
        assert inputs["encoding"] == "CSV", \
            "At the moment the only support is provided for CSV data"
        assert outputs["encoding"] == "CSV", \
            "At the moment the only support is provided for CSV data"

        schema = SchemaDescription(
            self._parse_data("input", inputs['data']),
            self._parse_data("output", outputs['data'])
        )
        logger.debug("Inferred schemas with %d inputs and %d outputs",
                     len(schema.inputs), len(schema.outputs))
        return schema

    def _parse_data(self, prefix: str, row: str) -> List[ColumnDescription]:
        """Infer column schemas based on the input CSV row."""
        logger.debug("Inferencing a row schema")
        dataframe = pd.read_csv(StringIO(row), header=None)
        return [
            ColumnDescription(
                f"{prefix}_{i}",
                dataframe.dtypes[i].name,
                DTYPE_CONVERSIONS.get(dataframe.dtypes[i].name),
                dataframe.dtypes[i].shape,
            )
            for i in range(len(dataframe.columns))
        ]

    def _update_headers(self):
        """
        Substitute synthetic headers with ones, extracted from a given bucket/key.
        """
        logger.debug("Substituting header names")
        dataframe = pd.read_csv(BytesIO(next(self.train_record.read())))
        descriptions = chain(reversed(self.schema.inputs), reversed(self.schema.outputs))
        for new_name, desc in zip(reversed(dataframe.columns), descriptions):
            desc.name = new_name


class Request:
    """A single request, processed by a Sagemaker model."""
    __slots__ = ('inputs', 'outputs', 'metadata')

    def __init__(
            self,
            inputs: List[Column],
            outputs: List[Column],
            metadata: Metadata
    ) -> 'Request':
        self.inputs = inputs
        self.outputs = outputs
        self.metadata = metadata

    @classmethod
    def from_dict(cls, data: Dict, schema: SchemaDescription) -> 'Request':
        """Create a new Request instance from a raw json line."""
        input_data = data['captureData']['endpointInput']['data'].split(',')
        output_data = data['captureData']['endpointOutput']['data'].split(',')
        inputs = [
            Column(description, data)
            for description, data in zip(schema.inputs, input_data)
        ]
        outputs = [
            Column(description, data)
            for description, data in zip(schema.outputs, output_data)
        ]
        metadata = Metadata(
            data['eventMetadata']['eventId'],
            data['eventMetadata']['inferenceTime']
        )
        return cls(inputs, outputs, metadata)

    def build_input_tensors(self) -> Dict:
        return {
            column.description.name: hs.TensorProto(
                **self._build_tensor_kwargs(column)
            )
            for column in self.inputs
        }

    def build_output_tensors(self) -> Dict:
        return {
            column.description.name: hs.TensorProto(
                **self._build_tensor_kwargs(column)
            )
            for column in self.outputs
        }

    def _build_tensor_kwargs(self, column: Column) -> Dict:
        """Build keyword arguments for tensor constraction."""
        kwargs = {"dtype": column.description.htype}
        value_field = VALUE_CONVERSIONS.get(column.description.htype)
        value = pd.read_csv(StringIO(column.data), header=None)
        value = value.iloc[0].astype(column.description.dtype)
        kwargs[value_field] = value.values
        kwargs["tensor_shape"] = hs.TensorShapeProto(dim=[
            hs.TensorShapeProto.Dim(size=shape)
            for shape in column.description.shape
        ])
        return kwargs
