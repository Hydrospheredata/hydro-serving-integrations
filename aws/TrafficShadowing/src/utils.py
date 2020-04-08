"""
This module contains utility function for performing traffic shadowing.
"""
import os
import logging
import urllib.parse
from io import StringIO
from typing import Tuple, Dict
import boto3
import pandas as pd
import numpy as np
import hydro_serving_grpc as hs
from src import errors
from src.data import Column

logger = logging.getLogger('main')
s3_client = boto3.client('s3')


DTYPE_CONVERSIONS = {
    "string":       "DT_STRING",
    "bool":         "DT_BOOL",
    "variant":      "DT_VARIANT",

    "float16":      "DT_HALF",
    "half":         "DT_HALF",
    "float32":      "DT_FLOAT",
    "float64":      "DT_DOUBLE",
    "double":       "DT_DOUBLE",

    "int8":         "DT_INT8",
    "int16":        "DT_INT16",
    "int32":        "DT_INT32",
    "int64":        "DT_INT64",

    "uint8":        "DT_UINT8",
    "uint16":       "DT_UINT16",
    "uint32":       "DT_UINT32",
    "uint64":       "DT_UINT64",

    "qint8":        "DT_QINT8",
    "qint16":       "DT_QINT16",
    "qint32":       "DT_QINT32",

    "quint8":       "DT_QUINT8",
    "quint16":      "DT_QUINT16",

    "complex64":    "DT_COMPLEX64",
    "complex128":   "DT_COMPLEX128",
}

PROFILE_CONVERSIONS = {
    "string":       "TEXT",
    "bool":         "NONE",
    "variant":      "NONE",

    "float16":      "NUMERICAL",
    "half":         "NUMERICAL",
    "float32":      "NUMERICAL",
    "float64":      "NUMERICAL",
    "double":       "NUMERICAL",

    "int8":         "NUMERICAL",
    "int16":        "NUMERICAL",
    "int32":        "NUMERICAL",
    "int64":        "NUMERICAL",

    "uint8":        "NUMERICAL",
    "uint16":       "NUMERICAL",
    "uint32":       "NUMERICAL",
    "uint64":       "NUMERICAL",

    "qint8":        "NUMERICAL",
    "qint16":       "NUMERICAL",
    "qint32":       "NUMERICAL",

    "quint8":       "NUMERICAL",
    "quint16":      "NUMERICAL",

    "complex64":    "NONE",
    "complex128":   "NONE",
}

VALUE_CONVERSIONS = {
    "DT_STRING":        "string_val",
    "DT_BOOL":          "bool_val",

    "DT_HALF":          "half_val",
    "DT_FLOAT":         "float_val",
    "DT_DOUBLE":        "double_val",

    "DT_INT8":          "int_val",
    "DT_INT16":         "int_val",
    "DT_INT32":         "int_val",
    "DT_INT64":         "int64_val",

    "DT_UINT8":         "int_val",
    "DT_UINT16":        "int_val",
    "DT_UINT32":        "uint32_val",
    "DT_UINT64":        "uint64_val",

    "DT_COMPLEX64":     "scomplex_val",
    "DT_COMPLEX128":    "dcomplex_val",
}

def parse_s3_uri(uri: str) -> Tuple[str, str]:
    """
    Parse S3 URI to bucket, key tuple.
    """
    parse = urllib.parse.urlparse(uri)
    bucket = parse.netloc
    key = parse.path.strip('/')
    return bucket, key


def parse_model_name(capture_prefix: str, record_key: str) -> str:
    """
    Parses the name of the Sagemaker model from the S3 path.
    """
    logger.debug("Parsing a SageMaker model name from %s", record_key)
    env_parts_num = len(capture_prefix.split('/'))
    model_name = record_key.split('/')[env_parts_num]
    logger.debug("Parsed the model name: %s", model_name)
    return model_name


def parse_training_path(training_bucket: str, training_prefix: str, model_name: str) -> str:
    """
    Parses training path from the specified training prefix.
    """
    training_path = '/'.join([training_prefix, model_name])
    response = s3_client.list_objects_v2(Bucket=training_bucket, Prefix=training_path)
    contents = response.get('Contents')
    candidates = list(filter(lambda x: os.path.splitext(x['Key'])[1].lower() == '.csv', contents))
    if not candidates:
        raise errors.DataNotFound(f'Didn\'t find .csv training data under "{training_path}" path')
    candidates.sort(key=lambda x: x['Size'], reverse=True)
    return f"s3://{training_bucket}/{candidates[0]['Key']}"


def transform_model_name(name: str) -> str:
    """
    Transforms original SageMaker model name into a valid Docker container name.
    """
    new_name = name.lower()
    logger.debug("Transforming model name: %s -> %s", name, new_name)
    return new_name


def build_tensor_kwargs(column: Column) -> Dict:
    """
    Build keyword arguments for tensor constraction.
    """
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
