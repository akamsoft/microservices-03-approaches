import json
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify

app = Flask(__name__)

S3_ENDPOINT = os.environ['S3_ENDPOINT']
S3_ACCESS_KEY = os.environ['S3_ACCESS_KEY']
S3_SECRET_KEY = os.environ['S3_SECRET_KEY']
S3_BUCKET = os.environ.get('S3_BUCKET', 'images')

s3 = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name='us-east-1',
)


def ensure_bucket():
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=S3_BUCKET)
    # Публичное чтение — иначе GET /v1/user/{image} через nginx не сможет отдать файл.
    policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'AWS': ['*']},
            'Action': ['s3:GetObject'],
            'Resource': [f'arn:aws:s3:::{S3_BUCKET}/*'],
        }],
    }
    s3.put_bucket_policy(Bucket=S3_BUCKET, Policy=json.dumps(policy))


@app.post('/v1/upload')
def upload():
    data = request.get_data()
    if not data:
        return jsonify({'error': 'no file'}), 400
    key = f'{uuid.uuid4()}.jpg'
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType='image/jpeg')
    return jsonify({'image': key}), 201


if __name__ == '__main__':
    ensure_bucket()
    app.run(host='0.0.0.0', port=80)