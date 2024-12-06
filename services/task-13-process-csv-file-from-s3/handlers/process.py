import os
import json
import boto3
import botocore.exceptions
import pandas as pd
from datetime import datetime
import logging
import uuid
import uuid

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
s3_client = boto3.client('s3')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Task13Table')

def cleanup_tmp_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Successfully deleted {filepath}")
    except Exception as e:
        logger.error(f"Error deleting {filepath}: {str(e)}")

def fetch_and_store_data(event, context):
    try:
        body = json.loads(event['body'])
        logger.info(f"Body: {body}")
        
        csv_file_name = body['filename']
        tmp_file_path = f"/tmp/{csv_file_name}"
        s3_client.download_file(S3_BUCKET_NAME, csv_file_name, tmp_file_path)

        df = pd.read_csv(tmp_file_path)
        logger.info(f"Successfully downloaded and read the CSV file: {csv_file_name}")

        logger.info(f"Dataframe: {df}")

        items = df.to_dict('records')

        for item in items:
            item['id'] = str(uuid.uuid4())
            table.put_item(Item=item)

        return{
            'statusCode':200,
            'body':json.dumps({
                'message': 'File downloaded successfully',
                'row_count':len(df)
            })
        }

    
    except botocore.exceptions.ClientError as e:
        error_message = f"Error downloading file from s3: {str(e)}"
        logger.error(error_message)
        return{
            'statusCode':500,
            'body':json.dumps({'error':error_message})
        }
    
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON in request body : {str(e)}"
        logger.error(error_message)
        return{
            'statusCode':400,
            'body':json.dumps({'error':error_message})
        }
    
    except Exception as e:
        error_message = f"Unexpected error : {str(e)}"
        logger.error(error_message)
        return{
            'statusCode':500,
            'body':json.dumps({'error':error_message})
        }
    
    finally:
        cleanup_tmp_file(tmp_file_path)
    







