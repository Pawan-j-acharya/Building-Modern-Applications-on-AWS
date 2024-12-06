import boto3
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

cognito_client = boto3.client('cognito-idp')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

def confirm_signup(event, context):
    try:
        body = json.loads(event['body'])
        email = body['email']
        confirmation_code = body['code']
        
        logger.info(f"Attempting to verify email: {email}")

        response = cognito_client.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=confirmation_code
        )
        
        logger.info(f"Email verification successful for user: {email}")
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Email verified successfully',
                'email': email
            })
        }
    
    except cognito_client.exceptions.CodeMismatchException:
        logger.error("Invalid verification code")
    
    except cognito_client.exceptions.ExpiredCodeException:
        logger.error("Verification code has expired")
    
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': f'Error during verification: {str(e)}'
            })
        }

# Add resend verification function
def resend_verification(event, context):
    try:
        body = json.loads(event['body'])
        email = body['email']
        
        response = cognito_client.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID,
            Username=email
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Verification code resent successfully',
                'email': email
            })
        }
    
    except Exception as e:
        logger.error(f"Error resending code: {str(e)}")

