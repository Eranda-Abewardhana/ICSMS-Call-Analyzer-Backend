from concurrent.futures import ThreadPoolExecutor
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
                return True
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
