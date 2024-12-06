import boto3
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

cognito_client = boto3.client('cognito-idp')
COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

def handler(event,context):

    body = json.loads(event['body'])
    username = body['username']
    password = body['password']
    email = body['email']

    try:
        response = cognito_client.sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'name',
                    'Value': username
                }
            ]
        )
        logging.info(response)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User signed up successfully'})
        }
    
    except cognito_client.exceptions.UsernameExistsException as e:
        logging.error(e)
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Username already exists'})
        }
    
    except cognito_client.exceptions.InvalidPasswordException as e:
        logging.error(e)
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid password'})
        }
    
    except Exception as e:
        logging.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error signing up user'})
        }