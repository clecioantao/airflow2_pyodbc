from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from elasticsearch_plugin.hooks.elastic_hook import ElasticHook

from datetime import datetime

default_args = {
    'start_date': datetime(2020, 1, 1)
}

def _print_es_info():
    hook = ElasticHook
    print(hook.info())


with DAG('elasticsearch_dag', schedule_interval='@daily', default_args=default_args, catchup=False, tags=['curso1', 'marc']) as dag:

    print_es_info = PythonOperator(
        task_id='print_es_info',
        python_callable=_print_es_info
    )