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


def initialize_airflow():
    logging.info('Creating connections, pools, etc.')

    session = Session()

    # CONNECTIONS
    new_connection(
        session,
        conn_id="my_postgres",
        conn_type="postgres",
        host="postgres",
        port=5432,
        schema="airflow",
        login="airflow",
        password="airflow")

    # POOLS
    new_pool(session, name="mypool", slots=10, description="Allows mox. 10 connections.")
    # Make sure failure handling works.
    new_pool(session, name="mypool", slots=10, description="Allows mox. 10 connections.")

    # CHARTS
    # FYI ATM graphs in Airflow are broken, use datatables for now.
    new_chart(
        session,
        conn_id='my_postgres',
        label='Active Task Instances by State',
        sql="""SELECT state, COUNT(*)
    FROM task_instance
    WHERE state NOT IN ('success', 'failed')
    GROUP BY state
    ORDER BY COUNT(*)
    """
    )

    new_chart(
        session,
        conn_id='my_postgres',
        label='Scheduler Delay (Last 2 Hours)',
        sql="""SELECT execution_date as "Execution Date",
       (EXTRACT(epoch FROM start_date) - EXTRACT(epoch FROM execution_date)) / 60 "Scheduler Delay (min)"
FROM dag_run
WHERE dag_id = 'canary'
AND execution_date >= NOW() - INTERVAL '2 hour'
ORDER BY "Execution Date" DESC;
"""
    )

    new_chart(
        session,
        conn_id='my_postgres',
        label='Scheduler Delay (Aggregated per hour)',
        sql="""SELECT DATE_TRUNC('hour', execution_date) as "Execution Hour",
       AVG((EXTRACT(epoch FROM start_date) - EXTRACT(epoch FROM execution_date)) / 60) " Average Scheduler Delay (min)"
FROM dag_run
WHERE dag_id = 'canary'
AND execution_date >= NOW() - INTERVAL '7 day'
GROUP BY DATE_TRUNC('hour', execution_date)
ORDER BY "Execution Hour" DESC;
"""
    )

    session.close()


with airflow.DAG('init_airflow', schedule_interval="@once", default_args=args) as dag:
    t1 = PythonOperator(task_id='initialize_etl_example', python_callable=initialize_airflow, provide_context=False)


# Helpers

def new_chart(session, conn_id, label, sql, chart_type='datatable', sql_layout="columns", x_is_date=False):
    logging.info("Creating new chart: {}".format(label))
    chart = models.Chart()

    chart.conn_id = conn_id
    chart.label = label
    chart.sql = sql
    chart.chart_type = chart_type
    chart.sql_layout = sql_layout
    chart.x_is_date = x_is_date

    try:
        session.add(chart)
        session.commit()
    except Exception as err:
        session.rollback()
        logging.error(err)


def new_connection(session, conn_id, conn_type, host, port, schema, login, password):
    logging.info("Creating new connection: {}".format(conn_id))
    connection = models.Connection()

    connection.conn_id = conn_id
    connection.conn_type = conn_type
    connection.host = host
    connection.port = port
    connection.schema = schema
    connection.login = login
    connection.password = password

    try:
        session.add(connection)
        session.commit()
    except Exception as err:
        session.rollback()
        logging.error(err)


def new_pool(session, name, slots, description):
    logging.info("Creating new pool: {}".format(name))
    pool = models.Pool()

    pool.pool = name
    pool.slots = slots
    pool.description = description

    try:
        session.add(pool)
        session.commit()
    except Exception as err:
        session.rollback()
        logging.error(err)


def delete_connection(session, conn_id):
    """Delete connection by a given conn_id."""

    conn = session.query(models.Connection).filter_by(conn_id=conn_id).first()
    if conn is None:
        raise Exception("Connection '%s' doesn't exist" % conn_id)

    session.delete(conn)
    session.commit()
