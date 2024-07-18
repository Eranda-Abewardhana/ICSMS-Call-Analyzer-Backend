from concurrent.futures import ThreadPoolExecutor
import re

import boto3
from botocore.exceptions import ClientError


class CancelledError(Exception):
    pass


def upload_to_s3(file_path, bucket_name, object_name, aws_access_key_id, aws_secret_access_key):
    try:
        with open(file_path, mode='rb') as file:
            data = file.read()

            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )

            def upload_file():
                return s3_client.put_object(
                    Bucket=bucket_name,
                    Key=object_name,
                    Body=data,
                )

            with ThreadPoolExecutor() as executor:
                response = executor.submit(upload_file).result()

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print(f"File {object_name} uploaded successfully to {bucket_name}")
            else:
                print(f"Unexpected response uploading file {object_name}: {response}")
                return False

    except CancelledError:
        print(f"Upload of {object_name} was cancelled")
        raise
    except ClientError as e:
        print(f"ClientError uploading file {object_name}: {e}")
        raise
    except Exception as e:
        print(f"Error uploading file {object_name}: {e}")
        raise
    finally:
        if s3_client:
            s3_client.close()


def delete_from_s3(recording_url, aws_access_key_id, aws_secret_access_key):
    try:
        # Extract the bucket name and object key from the URL
        match = re.match(r'https://(.+?)\.s3\.amazonaws\.com/(.+)', recording_url)
        if not match:
            print(f"Invalid S3 URL: {recording_url}")
            return False

        bucket_name = match.group(1)
        object_key = match.group(2)

        # Create an S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        # Delete the object
        response = s3_client.delete_object(Bucket=bucket_name, Key=object_key)

        # Check if the deletion was successful
        if response['ResponseMetadata']['HTTPStatusCode'] == 204:
            print(f"File {object_key} deleted successfully from {bucket_name}")
            return True
        else:
            print(f"Unexpected response deleting file {object_key}: {response}")
            return False

    except ClientError as e:
        print(f"ClientError deleting file {object_key}: {e}")
        raise
    except Exception as e:
        print(f"Error deleting file {object_key}: {e}")
        raise
    finally:
        if s3_client:
            s3_client.close()
