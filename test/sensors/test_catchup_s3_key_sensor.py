from unittest import mock
import unittest
from parameterized import parameterized

from airflow.exceptions import AirflowException
from airflow.sensors.catchup_s3_key_sensor import CatchUpS3KeySensor


class CatchUpS3KeySensorTests(unittest.TestCase):

    def test_bucket_name_none_and_bucket_key_as_relative_path(self):
        """
        Test if exception is raised when bucket_name is None
        and bucket_key is provided as relative path rather than s3:// url.
        :return:
        """
        with self.assertRaises(AirflowException):
            CatchUpS3KeySensor(
                task_id='s3_key_sensor',
                bucket_key="file_in_bucket")

    def test_bucket_name_provided_and_bucket_key_is_s3_url(self):
        """
        Test if exception is raised when bucket_name is provided
        while bucket_key is provided as a full s3:// url.
        :return:
        """
        with self.assertRaises(AirflowException):
            CatchUpS3KeySensor(
                task_id='s3_key_sensor',
                bucket_key="s3://test_bucket/file",
                bucket_name='test_bucket')

    @parameterized.expand([
        ['s3://bucket/key', None, 'key', 'bucket'],
        ['key', 'bucket', 'key', 'bucket'],
    ])
    def test_parse_bucket_key(self, key, bucket, parsed_key, parsed_bucket):
        s = CatchUpS3KeySensor(
            task_id='s3_key_sensor',
            bucket_key=key,
            bucket_name=bucket,
        )
        self.assertEqual(s.bucket_key, parsed_key)
        self.assertEqual(s.bucket_name, parsed_bucket)

    @mock.patch('airflow.hooks.S3_hook.S3Hook')
    def test_poke(self, mock_hook):
        s = CatchUpS3KeySensor(
            task_id='s3_key_sensor',
            bucket_key='s3://test_bucket/file')

        mock_check_for_key = mock_hook.return_value.check_for_key
        mock_check_for_key.return_value = False
        self.assertFalse(s.poke(None))
        mock_check_for_key.assert_called_with(s.bucket_key, s.bucket_name)

        mock_hook.return_value.check_for_key.return_value = True
        self.assertTrue(s.poke(None))

    @mock.patch('airflow.hooks.S3_hook.S3Hook')
    def test_poke_wildcard(self, mock_hook):
        s = CatchUpS3KeySensor(
            task_id='s3_key_sensor',
            bucket_key='s3://test_bucket/file',
            wildcard_match=True)

        mock_check_for_wildcard_key = mock_hook.return_value.check_for_wildcard_key
        mock_check_for_wildcard_key.return_value = False
        self.assertFalse(s.poke(None))
        mock_check_for_wildcard_key.assert_called_with(s.bucket_key, s.bucket_name)

        mock_check_for_wildcard_key.return_value = True
        self.assertTrue(s.poke(None))
