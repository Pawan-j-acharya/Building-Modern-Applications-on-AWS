import json
import os
import boto3
import logging

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)

# Add new handler
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('WebSocketConnections')

def get_api_client(event):
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    endpoint = f'https://{domain}/{stage}'
    return boto3.client('apigatewaymanagementapi', endpoint_url=endpoint)

def connect(event, context):
    connection_id = event['requestContext']['connectionId']
    name = event['queryStringParameters']['name']
    table.put_item(Item={'connectionId': connection_id,"name":name})
    
    logger.info(f'New connection: {connection_id} and name:{name}')
    
    return{
        'statusCode': 200,
        'body': json.dumps('Connected to websocket!!')
    }

def disconnect(event, context):
    connection_id = event['requestContext']['connectionId']
    table.delete_item(Key={'connectionId': connection_id})
    
    logger.info(f'Disconnected: {connection_id}')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Disconnected from websocket!!')
    }

def message(event, context):
    try:
        connection_id = event['requestContext']['connectionId']
        user_name = table.get_item(Key={'connectionId': connection_id})['Item']['name']
        logger.info(f"User name: {user_name}")
        message = event['body']

        # Get API client with correct endpoint
        apigatewaymanagementapi = get_api_client(event)

        connections = table.scan()['Items']
        logger.info(f"Connections: {connections}")

        for connection in connections:
            target_connection_id = connection['connectionId']
            if target_connection_id == connection_id:
                continue
            logger.info(f"Sending message to : {target_connection_id}")
            logger.info(f'Message :{message}')
            try:
                apigatewaymanagementapi.post_to_connection(
                    ConnectionId=target_connection_id,
                    Data=json.dumps(f"{user_name} :- {message}").encode('utf-8')  
                )
                logger.info(f"Message sent to connection: {target_connection_id}")

            except apigatewaymanagementapi.exceptions.GoneException:
                logger.warning(f"Removing stale connection: {target_connection_id}")
                table.delete_item(Key={'connectionId': target_connection_id})

            except Exception as e:
                logger.error(f"Error sending message to {target_connection_id}: {str(e)}")

        return {
            'statusCode': 200,
            'body': json.dumps('Message sent to all connected clients!')
        }

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to process message!')
        }
