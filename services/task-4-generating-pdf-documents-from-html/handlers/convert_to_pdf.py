# handler.py
import json
import base64
import boto3
import os
from weasyprint import HTML, CSS
from datetime import datetime
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
BUCKET_NAME = os.environ['PDF_BUCKET_NAME']
PRESIGNED_URL_EXPIRATION = 3600  # URL expires in 1 hour

def handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        html_content = body.get('html')
        css_content = body.get('css', '')
        filename = body.get('filename', f'document_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')

        if not html_content:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'HTML content is required'})
            }

        # Generate PDF
        css = CSS(string=css_content)
        pdf = HTML(string=html_content).write_pdf(stylesheets=[css])
        
        # Upload to S3
        try:
            s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=pdf, ContentType='application/pdf')
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to upload to S3: {str(e)}'})
            }

        # Generate presigned URL for download
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': BUCKET_NAME,
                    'Key': filename
                },
                ExpiresIn=PRESIGNED_URL_EXPIRATION
            )
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to generate presigned URL: {str(e)}'})
            }

        # Convert PDF to base64 for direct response
        pdf_base64 = base64.b64encode(pdf).decode('utf-8')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'pdf': pdf_base64,
                's3_key': filename,
                'download_url': presigned_url,
                'url_expires_in': PRESIGNED_URL_EXPIRATION
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
