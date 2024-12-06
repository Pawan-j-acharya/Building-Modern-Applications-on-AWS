import json
import pandas as pd
import boto3
import botocore.exceptions
import os
from datetime import datetime
import logging 

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
EXPORT_BUCKET = os.environ['EXPORT_BUCKET']


def get_data(table_name, columns):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        logger.info(f"Table data: {table}")
        response = table.scan()
        data = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])

        if columns:
            return [{col: item[col] for col in columns} for item in data]
        else:
            return data
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error(f"Table '{table_name}' not found.")
            raise e
    except Exception as e:
        raise e

def handler(event, context):
    try:
        body = json.loads(event['body'])
        logger.info(f'Hey this is before event value access')
        table_name = body['table_name']
        logger.info(f'Hey this is after event value access')
        columns = body.get('columns', None)
        data = get_data(table_name, columns)

        df = pd.DataFrame(data)
        file_name = f"{table_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        df.to_csv(f"/tmp/{file_name}", index=False)

        s3_client.upload_file(f"/tmp/{file_name}", EXPORT_BUCKET, file_name)

        return {
            'statusCode': 200,
            'body': json.dumps(f"Data exported to {file_name} in bucket {EXPORT_BUCKET}")
        }
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return {
                'statusCode': 404,
                'body': json.dumps(f"Table '{table_name}' not found.")
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }