from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

from utils.parser import process_financials_data, write_to_stream


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

def _process_data():
    ret = process_financials_data()
    write_to_stream(ret, data_type='json', file_name='out.txt')

process_data_task = PythonOperator(task_id="process_data", python_callable=_process_data, dag=dag)

print_done_task = BashOperator(task_id="print_done", bash_command="echo Done!", dag=dag)

process_data_task >> print_done_task
