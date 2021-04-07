from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'start_date': datetime(2021, 1, 1),
    'schedule_interval': '@daily', # None, '@once', '@hourly', '@daily', etc.
    # These are optional
    # 'owner': 'ozbaya',
    # 'tags'=['ozbay'],
    # 'depends_on_past': False,
    # 'email': ['ozbaya@airflow.com'],
    # 'email_on_failure': False,
    # 'email_on_retry': False,
    # 'retries': 1,
    # 'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'catchup': False,
}


dag = DAG('super_simple_dag', default_args=default_args)
t1 = BashOperator(task_id="print_date1", bash_command="date", dag=dag)
t2 = BashOperator(task_id="sleep1", bash_command="sleep 5", retries=3, dag=dag)
t3 = BashOperator(task_id="print_done1", bash_command="echo Done 1!", dag=dag)
t4 = BashOperator(task_id="echo_exec_date", bash_command="echo execution date: {{ execution_date }}", dag=dag)
t1 >> t2 >> t3 >> t4


# with DAG('super_simple_dag_v2', default_args=default_args) as dag:
#     t1 = BashOperator(task_id="print_date2", bash_command="date")
#     t2 = BashOperator(task_id="sleep2", bash_command="sleep 5", retries=3)
#     t3 = BashOperator(task_id="print_done2", bash_command="echo Done 2!")
#     t4 = BashOperator(task_id="echo_exec_date", bash_command="echo execution date: {{ execution_date }}")
#     t1 >> t2 >> t3 >> t4


# from airflow.decorators import dag
#
# @dag(default_args=default_args)
# def super_simple_dag_v3():
#     t1 = BashOperator(task_id="print_date3", bash_command="date")
#     t2 = BashOperator(task_id="sleep3", bash_command="sleep 5", retries=3)
#     t3 = BashOperator(task_id="print_done3", bash_command="echo Done 3!")
#     t4 = BashOperator(task_id="echo_exec_date", bash_command="echo execution date: {{ execution_date }}")
#     t1 >> t2 >> t3 >> t4
#
# my_dag = super_simple_dag_v3()
