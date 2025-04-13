import unittest
from unittest.mock import MagicMock, patch
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from io import BytesIO
from services.storage.object_store import S3MediaManager, MediaType

class TestS3MediaManager(unittest.TestCase):

    def setUp(self):
        self.framework_id = "test_framework"
        self.media_manager = S3MediaManager(framework_id=self.framework_id)
        self.media_type = MediaType.IMAGE
        self.filename = "test_file.jpg"
        self.bucket_name = self.media_manager.get_bucket_name(self.media_type)
        self.s3_key = self.media_manager._generate_s3_key(self.filename)
        self.file_data_bytes = b"test image data"

        # Mock the boto3 client
        self.mock_s3_client = MagicMock()
        self.media_manager._s3 = self.mock_s3_client

        # Mock the settings to avoid actual AWS credentials
        self.mock_settings = MagicMock()
        self.mock_settings.AWS_ACCESS_KEY_ID = "test_access_key"
        self.mock_settings.AWS_SECRET_ACCESS_KEY = "test_secret_key"
        self.mock_settings.AWS_REGION = "us-west-2"
        self.media_manager.settings = self.mock_settings

    def test_upload_file_success_bytes(self):
        self.mock_s3_client.put_object.return_value = {}
        success = self.media_manager.upload_file(
            file_data=self.file_data_bytes,
            media_type=self.media_type,
            filename=self.filename
        )
        self.assertTrue(success)
        self.mock_s3_client.put_object.assert_called_once_with(
            Bucket=self.bucket_name,
            Key=self.s3_key,
            Body=self.file_data_bytes
        )

    def test_upload_file_failure(self):
        self.mock_s3_client.put_object.side_effect = Exception("Upload failed")
        success = self.media_manager.upload_file(
            file_data=self.file_data_bytes,
            media_type=self.media_type,
            filename=self.filename
        )
        self.assertFalse(success)
        self.mock_s3_client.put_object.assert_called_once_with(
            Bucket=self.bucket_name,
            Key=self.s3_key,
            Body=self.file_data_bytes
        )

    def test_get_file_url_success(self):
        presigned_url = "https://s3.amazonaws.com/test_bucket/test_file.jpg?AWSAccessKeyId=XXX&Expires=1678886400&Signature=YYY"
        self.mock_s3_client.generate_presigned_url.return_value = presigned_url
        url = self.media_manager.get_file_url(filename=self.filename, media_type=self.media_type)
        self.assertEqual(url, presigned_url)
        self.mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": self.s3_key},
            ExpiresIn=3600
        )

    def test_get_file_url_failure(self):
        self.mock_s3_client.generate_presigned_url.side_effect = ClientError({'Error': {'Code': 'SomeError', 'Message': 'Something went wrong'}}, 'GetObject')
        url = self.media_manager.get_file_url(filename=self.filename, media_type=self.media_type)
        self.assertIsNone(url)
        self.mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": self.s3_key},
            ExpiresIn=3600
        )

    def test_delete_file_success(self):
        self.mock_s3_client.delete_object.return_value = {}
        success = self.media_manager.delete_file(filename=self.filename, media_type=self.media_type)
        self.assertTrue(success)
        self.mock_s3_client.delete_object.assert_called_once_with(
            Bucket=self.bucket_name,
            Key=self.s3_key
        )

    def test_delete_file_failure(self):
        self.mock_s3_client.delete_object.side_effect = Exception("Delete failed")
        success = self.media_manager.delete_file(filename=self.filename, media_type=self.media_type)
        self.assertFalse(success)
        self.mock_s3_client.delete_object.assert_called_once_with(
            Bucket=self.bucket_name,
            Key=self.s3_key
        )

if __name__ == '__main__':
    unittest.main()