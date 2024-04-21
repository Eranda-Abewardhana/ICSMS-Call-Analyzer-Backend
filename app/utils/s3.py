import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import boto3


async def upload_to_s3(file_path, bucket_name, object_name, aws_access_key_id, aws_secret_access_key):
    try:
        async with aiofiles.open(file_path, mode='rb') as file:
            data = await file.read()
            # Create an S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )

            # Define a function to upload file in a synchronous manner
            def upload_file():
                return s3_client.put_object(
                    Bucket=bucket_name,
                    Key=object_name,
                    Body=data,
                )

            # Use ThreadPoolExecutor to run the synchronous S3 operation
            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(executor, upload_file)

            # Check response status
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print("File uploaded successfully")
            else:
                print("Error uploading file:", response)
    except Exception as e:
        print(f"Error uploading file: {e}")
