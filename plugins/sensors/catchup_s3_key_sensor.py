import datetime

from airflow.operators.sensors import BaseSensorOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults


class CatchUpS3KeySensor(BaseSensorOperator):
    """
    Replacement for airflows S3KeySensor that is useful in ETL scenarios.
    The key difference of this sensor to S3KeySensor is that it will flag success if data is not present,
    but the execution_date is <= datetime.utcnow() - datetime.timedelta(days=x).

    This particularly helps with DAGs that need to catch up.
    For recent DAGs this would behave exactly the same as a s3KeySensor.
    Waits for a key (a file-like instance on S3) to be present in a S3 bucket.
    S3 being a key/value it does not support folders. The path is just a key
    a resource.

    Args:
        s3_conn_id (str): Reference to s3 connection ID, default is usually fine.
        bucket_name (str): S3 bucket name to search.
        bucket_key (str): S3 bucket key within `bucket_name` to search.
        early_success_timedelta (datetime.timedelta): A time_delta to subtract from 'now' which defines at which point
        we auto mark key check as success even if there is no data.

    Returns:
        (bool) Poke method used to determine task instance success.
    """
    PASSED_WINDOW_LOG_TMPL = "No data found for key: {0}, execution_date: {1} is <= {2}. Marking Success"
    WITHIN_WINDOW_LOG_TMPL = "No data found for key: {0}, execution_date: {1} is > {2}. Retrying at next poke interval."
    DATA_EXISTS_TMPL = "Data exists for key: {0}"

    template_fields = ('bucket_key',)

    @apply_defaults
    def __init__(self,
                 bucket_name,
                 bucket_key,
                 early_success_timedelta=datetime.timedelta(days=7),
                 aws_conn_id='aws_default',
                 *args, **kwargs):

        super(CatchUpS3KeySensor, self).__init__(*args, **kwargs)

        self.aws_conn_id = aws_conn_id
        self.bucket_name = bucket_name
        self.bucket_key = bucket_key
        self.early_success_timedelta = early_success_timedelta

    def poke(self, context):
        data_exists = self.does_data_exist()

        if data_exists:
            self.log.info(self.DATA_EXISTS_TMPL.format(self.bucket_key))
            return True

        if context['execution_date'] <= datetime.datetime.utcnow() - self.early_success_timedelta:
            self.log.info(self.PASSED_WINDOW_LOG_TMPL
                          .format(self.bucket_key, context['execution_date'], self.early_success_timedelta))
            return True

        self.log.info(self.WITHIN_WINDOW_LOG_TMPL
                      .format(self.bucket_key, context['execution_date'], self.early_success_timedelta))
        return False

    def does_data_exist(self):
        from airflow.hooks.S3_hook import S3Hook

        self.log.info("Checking if data exists for key: {}".format(self.bucket_key))
        hook = S3Hook(aws_conn_id=self.aws_conn_id)
        return hook.check_for_key(self.bucket_key, self.bucket_name)


class CatchUpS3KeySensorPlugin(AirflowPlugin):
    name = "catch_up_s3_key_sensor_plugin"
    sensors = [CatchUpS3KeySensor]
