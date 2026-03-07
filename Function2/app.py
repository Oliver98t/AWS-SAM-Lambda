import boto3
import os
import json
import uuid

# define the DynamoDB table that Lambda will connect to
tablename = os.environ['TABLE_TABLE_NAME']

# create the DynamoDB resource
dynamo = boto3.client('dynamodb')

def lambda_handler(event, context):
    # get the message out of the SQS event
    message = event['Records'][0]['body']
    data = json.loads(message)
    print(data)
    # write event data to DDB table

    value = data['value']
    dynamo.put_item(
        TableName=tablename,
        Item={
            'id': {'S': str(uuid.uuid4())},
            'Value': {'S': str(value)}
        }
    )