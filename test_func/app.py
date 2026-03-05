import json

def lambda_handler(event, context):
    print(f"event: {event} \ncontetx: {context}")
    return {
        'statusCode': 200,
        'body': json.dumps('message from test func')
    }