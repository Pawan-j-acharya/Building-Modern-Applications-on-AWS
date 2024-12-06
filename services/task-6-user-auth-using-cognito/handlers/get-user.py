import boto3
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

cognito_client = boto3.client('cognito-idp')
COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

def get_user(event, context):
    try:
        
        authorization_header = event['headers'].get('Authorization')

        if not authorization_header:
            return {"statusCode": 400, "body": json.dumps({"error": "Authorization header is missing."})}
        
        access_token = authorization_header.split(" ")[1]
        
        logger.info(f"Access Token: {access_token}")

        response = cognito_client.get_user(AccessToken=access_token)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "User info retrieved", "data": response['UserAttributes']})
        }
    except cognito_client.exceptions.NotAuthorizedException:
        return {"statusCode": 403, "body": json.dumps({"error": "Invalid or expired access token."})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}