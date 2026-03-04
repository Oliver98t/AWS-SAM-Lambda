import boto3
import os
import json

# define the DynamoDB table that Lambda will connect to
tablename = os.environ['LAMBDAIACTABLE_TABLE_NAME']

# create the DynamoDB resource
dynamo = boto3.client('dynamodb')

def lambda_handler(event, context):
    print(f"event: {event} \ncontetx: {context}")
    '''
    # get the message out of the SQS event
    message = event['Records'][0]['body']
    data = json.loads(message)
    # write event data to DDB table
    if check_message_format(data):
        key = next(iter(data))
        value = data[key]
        dynamo.put_item(
            TableName=tablename,
            Item={
                'id': {'S': key},
                'Value': {'S': value}
            }
        )
    else:
        raise ValueError("Input data not in the correct format")
    #'''
    return {
        'statusCode': 200,
        'body': json.dumps('Message processed and stored in DynamoDB')
    }

# check that the event object contains a single key value  
# pair that can be written to the database
def check_message_format(message):
    if len(message) != 1:
        return False
        
    key, value = next(iter(message.items()))
    
    if not (isinstance(key, str) and isinstance(value, str)):
        return False

    else:
        return True
