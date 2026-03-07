import json
import boto3
import os

sqs = boto3.client('sqs')
queue_url = os.environ['SQSQUEUE1_QUEUE_URL']

def lambda_handler(event, context):
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({"value": 400})
    )
    return {
        'statusCode': 200,
        'body': json.dumps(f"Message sent to {queue_url}")
    }