# pylint: disable=missing-function-docstring
import json
from botocore.stub import Stubber
from src.data import (
    Record, Contract, Request
)
from tests.stubs.http.aws import GetObjectStub
from tests.config import (
    CAPTURE_BUCKET, CAPTURE_KEY, CAPTURE_FILENAME, TRAIN_BUCKET, TRAIN_KEY, TRAIN_FILENAME,
    SCHEMA,
)
from tests.config import s3_client, session


def test_record_read():
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(CAPTURE_BUCKET, CAPTURE_KEY, CAPTURE_FILENAME).generate_response()
        )

        record = Record(CAPTURE_BUCKET, CAPTURE_KEY, session)
        with open(CAPTURE_FILENAME, "r") as file:
            for local, remote in zip(file.readlines(), record.read()):
                assert local.strip() == remote.decode()


def test_contract_parse():
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(CAPTURE_BUCKET, CAPTURE_KEY, CAPTURE_FILENAME).generate_response()
        )

        capture_record = Record(CAPTURE_BUCKET, CAPTURE_KEY, session=session)
        contract = Contract(capture_record, session=session)
        assert len(contract.schema.inputs) == 4
        assert len(contract.schema.outputs) == 1


def test_contract_update_headers():
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(CAPTURE_BUCKET, CAPTURE_KEY, CAPTURE_FILENAME).generate_response()
        )
        s3_stubber.add_response(
            **GetObjectStub(TRAIN_BUCKET, TRAIN_KEY, TRAIN_FILENAME).generate_response()
        )
        capture_record = Record(CAPTURE_BUCKET, CAPTURE_KEY, session=session)
        train_record = Record(TRAIN_BUCKET, TRAIN_KEY, session=session)
        contract = Contract(capture_record, train_record, session=session)
        assert contract.schema == SCHEMA


def test_request_build_inputs():
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetObjectStub(CAPTURE_BUCKET, CAPTURE_KEY, CAPTURE_FILENAME).generate_response()
        )
        capture_record = Record(CAPTURE_BUCKET, CAPTURE_KEY, session=session)
        for line in capture_record.read():
            request = Request.from_dict(json.loads(line), SCHEMA)
            inputs = request.build_input_tensors()
            outputs = request.build_output_tensors()
            assert inputs["Account Length"].int64_val[0] == int(request.inputs[0].data)
            assert outputs["Churn"].double_val[0] == float(request.outputs[0].data)
        