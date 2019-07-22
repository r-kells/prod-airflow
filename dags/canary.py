from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash_operator import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2015, 6, 1),
    "email": ["alerts@airflow.com"],
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
}

with DAG("canary", default_args=default_args, schedule_interval=timedelta(minutes=5), catchup=False) as dag:
    t1 = BashOperator(task_id="print_date", bash_command="echo {{ ds }}")
