import boto3
import os
import json
import logging
import base64
from requests_toolbelt.multipart import decoder
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get bucket name from environment variable
BUCKET_NAME = os.environ.get('UPLOAD_BUCKET_NAME')
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

def validate_file(file_data):
    
    try:
        # Check if file data exists
        if not file_data:
            return False, "No file data provided"
        
        # Check file size
        file_size = len(file_data)
        if file_size > MAX_FILE_SIZE:
            return False, f"File size ({file_size} bytes) exceeds maximum limit of {MAX_FILE_SIZE} bytes"
        
        return True, ""
        
    except Exception as e:
        return False, str(e)

def get_file_metadata(filename, file_type):
   
    return {
        'ContentType': file_type or 'application/octet-stream',
        'Metadata': {
            'upload-date': datetime.now().isoformat(),
            'original-filename': filename
        }
    }

def upload_file_to_s3(file_data, filename, file_type, storage_class):
   
    try:
        # Validate bucket name
        if not BUCKET_NAME:
            raise ValueError("S3 bucket name not configured")

        # Validate file
        is_valid, error_message = validate_file(file_data)
        if not is_valid:
            raise ValueError(f"File validation failed: {error_message}")

        # Get file metadata
        extra_args = get_file_metadata(filename, file_type)
        extra_args['StorageClass'] = storage_class

        # Create S3 client
        s3_client = boto3.client('s3')

        # Generate unique object name (you could modify this based on your needs)
        object_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}/{filename}"

        # Upload file
        logger.info(f"Starting upload of {filename} to bucket {BUCKET_NAME}")
        
        s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=object_name,
        Body=file_data,
        **extra_args
        )


        # Generate presigned URL (optional, valid for 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': object_name},
            ExpiresIn=3600
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File uploaded successfully',
                'object_key': object_name,
                'bucket': BUCKET_NAME,
                'presigned_url': presigned_url
            })
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    except ClientError as e:
        logger.error(f"AWS S3 error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error uploading file to S3'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    logger.info(f"Event headers: {json.dumps(event.get('headers', {}))}")


    try:

        # Check if the event contains file data
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No file data provided'})
            }

        # Decode the body if it's base64-encoded
        is_base64_encoded = event.get('isBase64Encoded', False)
        body = base64.b64decode(event['body']) if is_base64_encoded else event['body']

        multipart_data = decoder.MultipartDecoder(body, event['headers']['Content-Type'].split('boundary=')[1])

        for part in multipart_data.parts:
                if part.headers.get('Content-Disposition'):
                    disposition = part.headers['Content-Disposition']
                    if 'file_data' in disposition:
                        file_data = part.content
                    elif 'filename' in disposition:
                        filename = part.content.decode('utf-8')
                    elif 'file_type' in disposition:
                        file_type = part.content.decode('utf-8')
        
        if not all([file_data, filename]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required file information'})
            }

        # Upload file to S3
        return upload_file_to_s3(file_data, filename, file_type, storage_class='STANDARD')

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error processing upload request -> {str(e)} '})
        }


