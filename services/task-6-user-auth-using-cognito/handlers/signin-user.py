import boto3
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

cognito_client = boto3.client('cognito-idp')
COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

def sign_in(event, context):
    try:
        logger.info(f"COGNITO_CLIENT_ID:{COGNITO_APP_CLIENT_ID}")

        body = json.loads(event['body'])
        email = body['email']
        password = body['password']

        response = cognito_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            },
            ClientId=str(COGNITO_APP_CLIENT_ID)
        )
        logging.info(response)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User signed in successfully' , "data": response['AuthenticationResult']})
        }
        
    except cognito_client.exceptions.NotAuthorizedException as e:
        logging.error(e)
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid username or password'})
        }
    
    except Exception as e:
        logging.error(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error signing in user'})
        }