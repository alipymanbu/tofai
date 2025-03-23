import boto3
import io
import os
from fastapi import UploadFile
from typing import Optional, BinaryIO
from config import settings

# Initialize S3 client
s3_client = boto3.client(
  's3',
  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
  region_name=settings.S3_REGION
)

async def upload_file(
  file: UploadFile, 
  folder: str = "uploads",
  session_id: Optional[str] = None
) -> str:
  """
  Upload a file to S3 storage.
  
  Args:
      file: The file to upload
      folder: The folder to upload to
      session_id: Optional session ID to organize files
      
  Returns:
      The URL of the uploaded file
  """
  # Generate path
  path = folder
  if session_id:
      path = f"{path}/{session_id}"
  
  # Generate unique filename
  filename = file.filename
  if not filename:
      filename = f"file_{hash(file)}"
  
  # Create full key (path)
  key = f"{path}/{filename}"
  
  # Read file content
  contents = await file.read()
  
  # Upload to S3
  s3_client.upload_fileobj(
      io.BytesIO(contents),
      settings.S3_BUCKET,
      key,
      ExtraArgs={
          "ContentType": file.content_type
      }
  )
  
  # Generate URL
  url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
  
  return url

async def upload_bytes(
  data: bytes,
  filename: str,
  content_type: str,
  folder: str = "uploads",
  session_id: Optional[str] = None
) -> str:
  """
  Upload bytes to S3 storage.
  
  Args:
      data: The bytes to upload
      filename: The filename to use
      content_type: The content type
      folder: The folder to upload to
      session_id: Optional session ID to organize files
      
  Returns:
      The URL of the uploaded file
  """
  # Generate path
  path = folder
  if session_id:
      path = f"{path}/{session_id}"
  
  # Create full key (path)
  key = f"{path}/{filename}"
  
  # Upload to S3
  s3_client.upload_fileobj(
      io.BytesIO(data),
      settings.S3_BUCKET,
      key,
      ExtraArgs={
          "ContentType": content_type
      }
  )
  
  # Generate URL
  url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
  
  return url

def get_download_url(key: str, expires_in: int = 3600) -> str:
  """
  Generate a temporary download URL for a file.
  
  Args:
      key: The S3 key (path) of the file
      expires_in: The expiration time in seconds
      
  Returns:
      A temporary download URL
  """
  return s3_client.generate_presigned_url(
      'get_object',
      Params={
          'Bucket': settings.S3_BUCKET,
          'Key': key
      },
      ExpiresIn=expires_in
  )

async def delete_file(key: str) -> bool:
  """
  Delete a file from S3.
  
  Args:
      key: The S3 key (path) of the file
      
  Returns:
      Whether the deletion was successful
  """
  try:
      s3_client.delete_object(
          Bucket=settings.S3_BUCKET,
          Key=key
      )
      return True
  except Exception as e:
      print(f"Error deleting file: {e}")
      return False