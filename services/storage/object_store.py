import mimetypes
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from botocore.config import Config
import os
import logging
from typing import Optional, Union
from enum import Enum
from config.settings import Settings  # Import the Settings class


class MediaType(str, Enum):
    IMAGE = "image"
    SPEECH = "speech"
    MUSIC = "music"
    VIDEO = "video"

class S3MediaManager:
    """
    A class for managing media files in an Amazon S3 bucket.

    This class provides methods for uploading, retrieving, deleting, and updating files,
    and uses a method to construct the bucket name with media type and framework ID.
    """

    def __init__(
        self,
        framework_id: str,
    ):
        """
        Initializes the S3MediaManager with framework ID and loads other settings from config.

        Args:
            framework_id: The ID of the framework. This will be part of the bucket name.
        """
        self.framework_id = framework_id
        self.settings = Settings()  # Load settings from the Settings class
        self.aws_access_key_id = self.settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = self.settings.AWS_SECRET_ACCESS_KEY
        self.region_name = self.settings.S3_REGION
        self._s3_key_prefix = ""  # Initialize with an empty string
        self._s3 = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            config=Config(signature_version='s3v4')
        )
    
    @classmethod
    def create_key(cls, session_id: str, framework_step_id: str, index: int, unique_key: str = "unique_key", content_type: str = "text/html") -> str:
        file_extension = mimetypes.guess_extension(content_type)
        return f"{session_id}-{framework_step_id}-{index}-{unique_key}.{file_extension}"

    def _check_connection(self):
        """
        Checks if the connection to S3 is established.  Raises an exception if not.
        """
        try:
            self._s3.list_buckets()  # A simple operation to check connection
        except NoCredentialsError:
            raise NoCredentialsError(
                "AWS credentials not found.  Please configure them correctly."
            )
        except ClientError as e:
            raise ClientError(f"Error connecting to S3: {e}", "ConnectError")

    @property
    def s3_key_prefix(self) -> str:
        """
        Getter for the S3 key prefix.

        Returns:
            The S3 key prefix.
        """
        return self._s3_key_prefix

    @s3_key_prefix.setter
    def s3_key_prefix(self, value: str):
        """
        Setter for the S3 key prefix.  Ensures the prefix does not start with
        a leading slash but ends with a trailing slash if it's not empty.

        Args:
            value: The S3 key prefix to set.
        """
        if not value:
            self._s3_key_prefix = ""  # Set to empty string if value is empty
        elif value.startswith("/"):
            self._s3_key_prefix = value[1:] + "/"
        elif not value.endswith("/"):
            self._s3_key_prefix = value + "/"
        else:
            self._s3_key_prefix = value

    def _generate_s3_key(self, filename: str) -> str:
        """
        Generates the full S3 key (path) for a given filename, combining the
        key prefix and the filename.

        Args:
            filename: The name of the file.

        Returns:
            The full S3 key.
        """
        return self.s3_key_prefix + filename

    def get_bucket_name(self, media_type: MediaType) -> str:
        """
        Constructs the bucket name based on media type and framework ID.

        Args:
            media_type: The type of media (e.g., MediaType.IMAGE).

        Returns:
            The bucket name string.
        """
        return f"{media_type.value}-{self.framework_id.replace('_', '-')}"

    def upload_file(
        self,
        file_data: bytes,
        media_type: MediaType,
        filename: str,
        ttl: Optional[int] = None,  # Add the ttl parameter
        content_type: str = "",
    ) -> bool:
        """
        Uploads a file to the S3 bucket. This version can upload from a file path or from bytes.

        Args:
            file_data: The data to upload.
            media_type: The type of media being uploaded (e.g., MediaType.IMAGE).
            filename: The name to use for the file in S3.
            ttl: Time-to-Live in seconds.  Optional.  If provided, the uploaded
                   object will be automatically deleted after this many seconds.

        Returns:
            True if the upload was successful, False otherwise.
        Raises:
            ValueError: If the media_type is invalid.
        """
        self._check_connection()  # Ensure we are connected.

        bucket_name = self.get_bucket_name(media_type)
        s3_key = self._generate_s3_key(filename)
        upload_args = {"Bucket": bucket_name, "Key": s3_key, "ContentType": content_type}
        # TODO: This ttl doesn't WAI. Implement liefecyle rules on buckets.
        if ttl is not None:
            upload_args["Expires"] = ttl

        try:
            self._s3.put_object(Body=file_data, **upload_args)
            logging.info(f"Bytes uploaded to s3://{bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logging.error(f"Error uploading to S3: {e}")
            return False

    def get_file_url(self, filename: str, media_type: MediaType) -> Optional[str]:
        """
        Generates a presigned URL for accessing a file in the S3 bucket.

        Args:
            filename: The name of the file in S3.
            media_type: The type of media (e.g., MediaType.IMAGE).

        Returns:
            The presigned URL if successful, None otherwise.
        Raises:
            ValueError: If the media_type is invalid.
        """
        self._check_connection()
        bucket_name = self.get_bucket_name(media_type)

        s3_key = self._generate_s3_key(filename)
        try:
            url = self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": s3_key},
                ExpiresIn=60 * 60 * 24 * 7,  # URL expires in 7 days
            )
            return url
        except ClientError as e:
            logging.info(f"Error generating URL for {filename}: {e}")
            return None

    def delete_file(self, filename: str, media_type: MediaType) -> bool:
        """
        Deletes a file from the S3 bucket.

        Args:
            filename: The name of the file in S3.
            media_type: The type of media (e.g., MediaType.IMAGE).

        Returns:
            True if the deletion was successful, False otherwise.
        Raises:
            ValueError: If the media_type is invalid.
        """
        self._check_connection()
        bucket_name = self.get_bucket_name(media_type)
        s3_key = self._generate_s3_key(filename)
        try:
            self._s3.delete_object(Bucket=bucket_name, Key=s3_key)
            logging.info(f"File s3://{bucket_name}/{s3_key} deleted.")
            return True
        except Exception as e:
            logging.info(f"Error deleting {filename} from S3: {e}")
            return False

    def list_files(self, media_type: MediaType, prefix: Optional[str] = None) -> list[str]:
        """
        Lists files in the S3 bucket, optionally with a prefix.

        Args:
            media_type: The type of media (e.g., MediaType.IMAGE).
            prefix:  The prefix to filter files. If None, lists all files.

        Returns:
            A list of file names (keys) in S3.
        Raises:
            ValueError: If the media_type is invalid.
        """
        self._check_connection()
        bucket_name = self.get_bucket_name(media_type)

        if prefix is None:
            prefix = self.s3_key_prefix
        else:
            prefix = self._generate_s3_key(prefix)  # make sure the prefix is correct

        try:
            response = self._s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            files = []
            if "Contents" in response:  # check if there are any files
                for obj in response["Contents"]:
                    files.append(obj["Key"])  # Return the full key (path)
            return files
        except Exception as e:
            logging.info(f"Error listing files in S3 with prefix {prefix}: {e}")
            return []

    def does_file_exist(self, filename: str, media_type: MediaType) -> bool:
        """
        Checks if a file exists in the S3 bucket.

        Args:
            filename: The name of the file to check.
            media_type: The type of media (e.g., MediaType.IMAGE).

        Returns:
            True if the file exists, False otherwise.
        Raises:
            ValueError: If the media_type is invalid.
        """
        self._check_connection()
        bucket_name = self.get_bucket_name(media_type)
        s3_key = self._generate_s3_key(filename)
        try:
            self._s3.head_object(Bucket=bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False  # File not found
            else:
                # Handle other errors (e.g., permission issues)
                logging.info(f"Error checking if file exists: {e}")
                return False
        except Exception as e:
            logging.info(f"Error checking file existence: {e}")
            return False

    def update_ttl(self, filename: str, media_type: MediaType, ttl: int) -> bool:
        """
        Updates the TTL of an existing object in S3 by copying the object
        with the new Expires parameter.

        Args:
            filename: The name of the file in S3.
            media_type: The type of media (e.g., MediaType.IMAGE).
            ttl: The new Time-to-Live in seconds.

        Returns:
            True if the TTL was updated successfully, False otherwise.
        Raises:
            ValueError: If the media_type is invalid.
        """
        self._check_connection()
        bucket_name = self.get_bucket_name(media_type)
        s3_key = self._generate_s3_key(filename)

        try:
            copy_source = {"Bucket": bucket_name, "Key": s3_key}
            self._s3.copy_object(
                Bucket=bucket_name,
                Key=s3_key,
                CopySource=copy_source,
                Expires=ttl,  # Set the new TTL here
            )
            logging.info(f"TTL for s3://{bucket_name}/{s3_key} updated to {ttl} seconds.")
            return True
        except Exception as e:
            logging.info(f"Error updating TTL for {filename}: {e}")
            return False

