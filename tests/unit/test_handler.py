import json
import pytest
from pytest_mock import MockerFixture

from Function1 import app as function1
from Function2 import app as function2


# --- Function1 tests ---

def test_function1_returns_200(mocker: MockerFixture):
    mocker.patch.dict('os.environ', {'SQSQUEUE1_QUEUE_URL': 'https://sqs.eu-west-2.amazonaws.com/123/test-queue'})
    mocker.patch.object(function1.sqs, 'send_message', return_value={})

    ret = function1.lambda_handler({}, {})

    assert ret['statusCode'] == 200


def test_function1_sends_correct_message(mocker: MockerFixture):
    queue_url = 'https://sqs.eu-west-2.amazonaws.com/123/test-queue'
    mocker.patch.dict('os.environ', {'SQSQUEUE1_QUEUE_URL': queue_url})
    mock_send = mocker.patch.object(function1.sqs, 'send_message', return_value={})

    function1.lambda_handler({}, {})

    mock_send.assert_called_once_with(
        QueueUrl=queue_url,
        MessageBody=json.dumps({'value': 400})
    )


def test_function1_body_contains_queue_url(mocker: MockerFixture):
    queue_url = 'https://sqs.eu-west-2.amazonaws.com/123/test-queue'
    mocker.patch.dict('os.environ', {'SQSQUEUE1_QUEUE_URL': queue_url})
    mocker.patch.object(function1.sqs, 'send_message', return_value={})

    ret = function1.lambda_handler({}, {})

    assert queue_url in ret['body']


# --- Function2 tests ---

@pytest.fixture()
def sqs_event():
    return {'Records': [{'body': json.dumps({'value': 400})}]}


def test_function2_writes_to_dynamodb(mocker: MockerFixture, sqs_event):
    mocker.patch.dict('os.environ', {'TABLE_TABLE_NAME': 'test-table'})
    mock_put = mocker.patch.object(function2.dynamo, 'put_item', return_value={})

    function2.lambda_handler(sqs_event, {})

    mock_put.assert_called_once()


def test_function2_writes_correct_value(mocker: MockerFixture, sqs_event):
    mocker.patch.dict('os.environ', {'TABLE_TABLE_NAME': 'test-table'})
    mock_put = mocker.patch.object(function2.dynamo, 'put_item', return_value={})

    function2.lambda_handler(sqs_event, {})

    call_args = mock_put.call_args[1]
    assert call_args['TableName'] == 'test-table'
    assert call_args['Item']['Value'] == {'N': '400'}


def test_function2_uses_correct_table(mocker: MockerFixture, sqs_event):
    mocker.patch.dict('os.environ', {'TABLE_TABLE_NAME': 'my-custom-table'})
    mock_put = mocker.patch.object(function2.dynamo, 'put_item', return_value={})

    function2.lambda_handler(sqs_event, {})

    call_args = mock_put.call_args[1]
    assert call_args['TableName'] == 'my-custom-table'
