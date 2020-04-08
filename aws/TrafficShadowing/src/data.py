"""
This module interacts with S3 data lake.
"""
import logging
import json
from typing import Generator, Dict, List, Tuple
from dataclasses import dataclass
from io import StringIO, BytesIO
from itertools import chain
import pandas as pd
import boto3
from src import utils

logger = logging.getLogger('main')
s3_client = boto3.client('s3')


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


class Request:
    """
    A single request, processed by a Sagemaker model.
    """
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
        """
        Creates a new Request instance from a raw json line.
        """
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


class Record:
    """
    Represents an object on S3 bucket and available operations
    on top of it.
    """
    def __init__(self, record: Dict) -> 'Record':
        self.bucket = record['s3']['bucket']['name']
        self.key = record['s3']['object']['key']

    def read_file(self) -> Generator[Dict, None, None]:
        """
        Reads downloaded file and yields its rows.
        """
        obj = s3_client.get_object(Bucket=self.bucket, Key=self.key)
        for line in obj['Body'].iter_lines():
            data = json.loads(line)
            yield data


class Contract:
    """
    Represents a contract for the model, inferred from file.
    """
    def __init__(self, record: Record) -> 'Contract':
        self.record = record
        self.__schema = None

    def _parse_schema(self) -> SchemaDescription:
        """
        Infers inputs and outputs of the model based on the downloaded
        file contents.
        """
        data = next(self.record.read_file())
        inputs = data['captureData']['endpointInput']
        outputs = data['captureData']['endpointOutput']
        assert inputs["encoding"] == "CSV", \
            "At the moment the only support is provided for CSV data"
        assert outputs["encoding"] == "CSV", \
            "At the moment the only support is provided for CSV data"

        self.__schema = SchemaDescription(
            self._parse_data("input", inputs['data']),
            self._parse_data("output", outputs['data'])
        )
        logger.debug("Inferred schemas with %d inputs and %d outputs",
                     len(self.__schema.inputs), len(self.__schema.outputs))
        return self.__schema

    def _parse_data(self, prefix: str, row: str) -> List[ColumnDescription]:
        """
        Infers column schemas based on the input CSV row.
        """
        logger.debug("Inferencing a row schema")
        dataframe = pd.read_csv(StringIO(row), header=None)
        return [
            ColumnDescription(
                f"{prefix}_{i}",
                dataframe.dtypes[i].name,
                utils.DTYPE_CONVERSIONS.get(dataframe.dtypes[i].name),
                dataframe.dtypes[i].shape,
            )
            for i in range(len(dataframe.columns))
        ]

    def update_headers(self, bucket: str, key: str):
        """
        Substitute synthetic headers with ones, extracted from the training
        data.
        """
        logger.debug("Substituting header names")
        iterator = s3_client.get_object(Bucket=bucket, Key=key)['Body'].iter_lines()
        dataframe = pd.read_csv(BytesIO(next(iterator)))
        descriptions = chain(reversed(self.schema.inputs), reversed(self.schema.outputs))
        for new_name, desc in zip(reversed(dataframe.columns), descriptions):
            desc.name = new_name

    @property
    def schema(self) -> SchemaDescription:
        """
        Lazy-loading schema from file.
        """
        if not self.__schema:
            self._parse_schema()
        return self.__schema
