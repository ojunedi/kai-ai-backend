from google.cloud import storage, secretmanager
from google.cloud import logging as cloud_logging
from fastapi import UploadFile
import os
import logging

def upload_to_gcs(file: UploadFile, bucket_name: str, blob_name: str):
    """
    Uploads a file to GCS and returns the public URL
    
    Args:
        file (UploadFile): The file to upload
        bucket_name (str): The bucket to upload to
        blob_name (str): The name of the blob to upload to
    
    Returns:
        str: The public URL of the uploaded file
    """
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    blob.upload_from_file(file.file.read(), content_type=file.content_type)
    file.file.close()
    
    return blob.public_url

def delete_from_gcs(bucket_name: str, blob_name: str):
    """
    Deletes a file from GCS
    
    Args:
        bucket_name (str): The bucket to delete from
        blob_name (str): The name of the blob to delete
    """
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    blob.delete()

def setup_logger(name=__name__):
    """
    Sets up a logger based on the environment.

    If the environment variable ENV_TYPE is set to 'sandbox' or 'production', it configures
    Google Cloud Logging. Otherwise, it returns an error.

    Parameters:
    name (str): The name of the logger.

    Returns:
    logging.Logger: Configured logger.
    """
    env_type = os.environ.get('ENV_TYPE', 'undefined')
    project = os.environ.get('PROJECT_ID', 'undefined')

    # Log the attempt to establish the logger
    print(f"Attempting to establish logger for {env_type} environment in project: {project}")

    if env_type in ['sandbox', 'production']:
        try:
            # Instantiates a client for Google Cloud Logging
            logging_client = cloud_logging.Client(project=project)
            # Retrieves a Cloud Logging handler based on the environment you're running in
            cloud_logging_handler = logging_client.get_default_handler()
            cloud_logger = logging.getLogger(name)
            cloud_logger.setLevel(logging.INFO)
            cloud_logger.addHandler(cloud_logging_handler)
            
            formatter = logging.Formatter(f'%(asctime)s - {env_type} - %(name)s - %(levelname)s - %(message)s')
            for handler in cloud_logger.handlers:
                handler.setFormatter(formatter)

            print(f"ESTABLISHED CLOUD LOGGER: {env_type} for project: {project}")
            return cloud_logger
        except Exception as e:
            print(f"Failed to configure Google Cloud Logging: {str(e)}")
            return logging.getLogger(name)  # Return a default logger if GCL fails
    else:
        error_message = f"Invalid environment type: {env_type}. Logger not configured."
        print(error_message)
        return Exception(error_message)

def access_secret_file(secret_id, version_id="latest"):
    """
    Access a secret file in Google Cloud Secret Manager and parse it.
    """
    project_id = os.environ.get('PROJECT_ID')
    print(f"Project ID: {project_id}")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")