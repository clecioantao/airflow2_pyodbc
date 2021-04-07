from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

from utils.callables import _process_data, _store_data, _check_for_content


default_args = {
    'start_date': datetime(2021, 1, 1),
    'owner': 'ozbaya',
    'depends_on_past': False,
    'email': ['ozbaya@airflow.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


dag = DAG('process_financials', default_args=default_args)


check_for_content_task = BranchPythonOperator(task_id="check_for_content", python_callable=_check_for_content, dag=dag)

print_no_data_task = BashOperator(task_id="print_no_data", bash_command="echo No data!", dag=dag)

process_data_task = PythonOperator(task_id="process_data", python_callable=_process_data, dag=dag)

store_data_task = PythonOperator(task_id="store_data", python_callable=_store_data, dag=dag)

print_done_task = BashOperator(task_id="print_done", bash_command="echo Done!", dag=dag)

db_insert_task = PostgresOperator(task_id="db_insert", postgres_conn_id="udemy_postgres_conn", dag=dag,
    sql=[
'''CREATE TABLE IF NOT EXISTS stock_financials (
    ticker varchar(50) not null,
    record_date date not null,
    timeframe varchar(10) not null,
    metric varchar(100) not null,
    value real,
    primary key (ticker, record_date, timeframe, metric)
);''',
'''insert into stock_financials
values {{ ti.xcom_pull(task_ids='store_data', key='return_value') }}
on conflict (ticker, record_date, timeframe, metric) do update set value = excluded.value''']
)


check_for_content_task >> [print_no_data_task, process_data_task]
process_data_task >> store_data_task >> db_insert_task >> print_done_task
