from airflow.models import DAG
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from airflow.providers.odbc.hooks.odbc import OdbcHook
from airflow.hooks.mssql_hook import MsSqlHook
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from pandas import json_normalize
import json
import sqlalchemy
import pandas as pd

default_args = {
    'start_date' : datetime(2021, 1, 1)
}

def _processing_user(ti):
    users = ti.xcom_pull(task_ids=['extracting_use'])
    if not len(users) or 'results' not in users[0]:
        raise ValueError('User is empty')
    user = users[0]['results'][0]
    processed_user = json_normalize({
        'firstname': user['name']['first'],
        'lastname': user['name']['last'],
        'country': user['location']['country'],
        'username': user['login']['username'],
        'password': user['login']['password'],
        'email': user['email']
    })

    processed_user.to_csv('/opt/airflow/dags/processed_user.csv', index=None, header=True)

    #print('processed_user',processed_user.country[0])

    data = [processed_user.firstname[0], 
            processed_user.lastname[0], 
            processed_user.country[0], 
            processed_user.username[0], 
            processed_user.password[0],
            processed_user.email[0]
    ]

    colunas = ['firstname','lastname','country','username','password','email']

    df = pd.DataFrame(data, colunas)
        
    #print(list(df))
    engineorigem = sqlalchemy.create_engine('mssql+pyodbc://sa:Proteu690201@192.168.2.120/bi_integracao?driver=ODBC+Driver+17+for+SQL+Server')
    #df.to_sql(name=users, con=engineorigem, if_exists='replace')


with  DAG('user_processing', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:
    # define tasks / operators

    creating_table = MsSqlOperator(
        task_id='creating_table',
        mssql_conn_id ='sql_server',
        database = 'bi_integracao',
        sql = '''
                CREATE TABLE users
                (
                firstname    varchar(100) NOT NULL,
                lastname     varchar(100) NOT NULL, 
                country      varchar(100) NOT NULL,
                username     varchar(100) NOT NULL,
                password     varchar(30)  NOT NULL,
                email        varchar(100) NOT NULL PRIMARY KEY
                )
              '''
    )

    is_api_available = HttpSensor(
        task_id = 'is_api_available',
        http_conn_id='user_api',
        endpoint='api/'
    )

    extract_user = SimpleHttpOperator (
        task_id = 'extracting_use',
        http_conn_id='user_api',
        endpoint='api/',
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True
    )

    processing_user = PythonOperator (
        task_id='processing_user',
        python_callable=_processing_user
    )
