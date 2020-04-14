import json
import pytest
import botocore
from botocore.stub import Stubber
from src.clients import ClientFactory
from src.data import (
    Record, Contract, Request, SchemaDescription, ColumnDescription
)
from tests.stubs.stubber import GetObjectStub

session = botocore.session.get_session()
s3_client = ClientFactory.get_client('s3', session)


@pytest.fixture
def bucket():
    return "bucket"


@pytest.fixture
def prefix():
    return "prefix"


@pytest.fixture
def model():
    return "model"


@pytest.fixture
def capture_key(prefix, model):
    # pylint: disable=redefined-outer-name
    return f"{prefix}/{model}/file.jsonl"


@pytest.fixture
def train_key(prefix, model):
    # pylint: disable=redefined-outer-name
    return f"{prefix}/{model}/file.csv"


@pytest.fixture
def capture_filename():
    return "aws/traffic_shadowing/tests/file.jsonl"


@pytest.fixture
def train_filename():
    return "aws/traffic_shadowing/tests/file.csv"


@pytest.fixture
def schema():
    return SchemaDescription(
        inputs=[
            ColumnDescription(
                name="Account Length",
                dtype="int64",
                htype="DT_INT64",
                shape=()
            ),
            ColumnDescription(
                name="VMail Message",
                dtype="float64",
                htype="DT_DOUBLE",
                shape=()
            ),
            ColumnDescription(
                name="Day Mins",
                dtype="float64",
                htype="DT_DOUBLE",
                shape=()
            ),
            ColumnDescription(
                name="Day Calls",
                dtype="int64",
                htype="DT_INT64",
                shape=()
            )
        ],
        outputs=[
            ColumnDescription(
                name="Churn",
                dtype="float64",
                htype="DT_DOUBLE",
                shape=()
            )
        ]
    )


def test_record_read(bucket, capture_key, capture_filename):
    # pylint: disable=redefined-outer-name
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(bucket, capture_key, capture_filename).generate_response()
        )

        record = Record(bucket, capture_key, session)
        with open(capture_filename, "r") as file:
            for local, remote in zip(file.readlines(), record.read()):
                assert local.strip() == remote.decode()


def test_contract_parse(bucket, capture_key, capture_filename):
    # pylint: disable=redefined-outer-name
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(bucket, capture_key, capture_filename).generate_response()
        )

        capture_record = Record(bucket, capture_key, session=session)
        contract = Contract(capture_record, session=session)
        assert len(contract.schema.inputs) == 4
        assert len(contract.schema.outputs) == 1


def test_contract_update_headers(
        bucket,
        capture_key,
        train_key,
        capture_filename,
        train_filename,
        schema
):
    # pylint: disable=redefined-outer-name
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(bucket, capture_key, capture_filename).generate_response()
        )
        s3_stubber.add_response(
            **GetObjectStub(bucket, train_key, train_filename).generate_response()
        )
        capture_record = Record(bucket, capture_key, session=session)
        train_record = Record(bucket, train_key, session=session)
        contract = Contract(capture_record, train_record, session=session)
        assert contract.schema == schema


def test_request_build_inputs(bucket, capture_key, capture_filename, schema):
    # pylint: disable=redefined-outer-name
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(bucket, capture_key, capture_filename).generate_response()
        )
        capture_record = Record(bucket, capture_key, session=session)
        for line in capture_record.read():
            request = Request.from_dict(json.loads(line), schema)
            inputs = request.build_input_tensors()
            outputs = request.build_output_tensors()
            assert inputs["Account Length"].int64_val[0] == int(request.inputs[0].data)
            assert outputs["Churn"].double_val[0] == float(request.outputs[0].data)
        