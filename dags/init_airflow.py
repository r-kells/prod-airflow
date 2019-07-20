import logging

import airflow
from airflow import models
from airflow.operators.python_operator import PythonOperator
from airflow.settings import Session

args = {
    'owner': 'airflow',
    "email": ["alerts@airflow.com"],
    'start_date': airflow.utils.dates.days_ago(1),
    'provide_context': True
}


def initialize_etl_example():
    logging.info('Creating connections, pools, etc.')

    session = Session()

    def delete_connection(session, conn_id):
        """Delete connection by a given conn_id."""

        conn = session.query(models.Connection).filter_by(conn_id=conn_id).first()
        if conn is None:
            raise Exception("Connection '%s' doesn't exist" % conn_id)

        session.delete(conn)
        session.commit()

        return conn_id

    def create_new_conn(session, attributes):

        new_conn = models.Connection()
        new_conn.conn_id = attributes.get("conn_id")
        new_conn.conn_type = attributes.get('conn_type')
        new_conn.host = attributes.get('host')
        new_conn.port = attributes.get('port')
        new_conn.schema = attributes.get('schema')
        new_conn.login = attributes.get('login')
        new_conn.set_password(attributes.get('password'))

        session.add(new_conn)
        session.commit()

    # delete_connection(session, 'postgres_default')
    create_new_conn(session,
                    {"conn_id": "my_postgres",
                     "conn_type": "postgres",
                     "host": "postgres",
                     "port": 5432,
                     "schema": "airflow",
                     "login": "airflow",
                     "password": "airflow"})

    new_pool = models.Pool()
    new_pool.pool = "mypool"
    new_pool.slots = 10
    new_pool.description = "Allows max. 10 connections to my_default process."

    session.add(new_pool)
    session.commit()

    new_chart = models.Chart()
    new_chart.conn_id = "my_postgres"
    new_chart.label = "Active Task Instance States"
    new_chart.sql = "SELECT state, COUNT(*) from task_instance WHERE state NOT IN ('success', 'failed') GROUP BY state ORDER BY COUNT(*)"
    new_chart.chart_type = "datatable"
    new_chart.x_is_date = False
    new_chart.sql_layout = "columns"

    session.add(new_chart)
    session.commit()

    session.close()


dag = airflow.DAG(
    'init_airflow',
    schedule_interval="@once",
    default_args=args,
    max_active_runs=1)

t1 = PythonOperator(task_id='initialize_etl_example',
                    python_callable=initialize_etl_example,
                    provide_context=False,
                    dag=dag)
