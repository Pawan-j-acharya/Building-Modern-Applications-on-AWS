import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('processed-text-data')

def send_message(event, context):
    try:
        logger.info("send_message function invoked!!")
        body = json.loads(event['body'])
        message = body.get('message')

        if not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error':'Message is required'})
            }
        
        queue_url = sqs.get_queue_url(
            QueueName='simple-processing-queue'
        )['QueueUrl']

        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({'message':message})
        )

        logger.info(f"Message sent to SQS: {message}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': "Message sent successfully",
                'messageId': response['MessageId']
            })
        }
    
    except ClientError as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error':'Failed to send Message'})
        }

def process_message(event, context):
    logger.info("process_message function invoked!!")
    try:
        for record in event['Records']:
            message_body = json.loads(record['body'])
            original_message = message_body['message']

            # Process the message (convert to uppercase)
            processed_message = original_message.upper()

            logger.info(f"Original message: {original_message}")
            logger.info(f"Processed message: {processed_message}")

            # Store in DynamoDB with the correct schema
            item = {
                'processed_data': processed_message  # This must match the hash key name
            }
            
            logger.info(f"Attempting to store item in DynamoDB: {item}")
            
            # Store in DynamoDB
            table.put_item(Item=item)
            
            logger.info("Message successfully stored in DynamoDB")
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise e
