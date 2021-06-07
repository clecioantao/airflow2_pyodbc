# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 13:31:57 2021
@author: Clecio Antao
Rotina para leitura de API Desk Manager para popular tabela SQL Server
"""

from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.email_operator import EmailOperator
#from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago

dag = DAG(
    "streaming_desk",
    default_args={
        "owner": "airflow",
        'email': ['clecio.antao@gmail.com'],
        'email_on_failure': True,
    },
    schedule_interval='*/5 * * * *',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=4),
    tags=['etl'],
)

def carrega_dados_desk():

    import pandas as pd
    import requests
    import json
    from es_pandas import es_pandas # modulo para integrar com elasticsearch

    # Dados do Elasticsearch
    es_host = '192.168.2.120:9200'
    index = 'chamados'

    # Cria instancia es_pandas 
    ep = es_pandas(es_host)

    # AUTENTICAÇÃO API DESK MANAGER
    url = "https://api.desk.ms/Login/autenticar"
    pubkey = '\"ef89a6460dbd71f2e37a999514d2543b99509d4f\"'
    payload=" {\r\n  \"PublicKey\" :" + pubkey + "\r\n}"
    headers = {
    'Authorization': '66e22b87364fa2946f2ce04dce1b8b59b669ab7f',
    'Content-Type': 'application/json'
    }
    token = requests.request("POST", url, headers=headers, data=payload)
    resp_token = json.loads(token.text)

    # BUSCA RELATORIO NA API DESK MANAGER
    url = "https://api.desk.ms/Relatorios/imprimir"
    paginador = '\"' +  '0' + '\"'
    relatorio = "875"
    payload="{\r\n  \"Chave\" :"  + relatorio +  ", \r\n  \"APartirDe\" :" + paginador + ", \r\n  \"Total\": \"\" \r\n}"
    headers = {
    'Authorization': resp_token,
    'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data=payload)
    resp_data = json.loads(resp.text)
    root = resp_data['root']
    df = pd.DataFrame(root)
    ############################
    
    # Inicia o template
    doc_type = 'chamados'
    ep.init_es_tmpl(df, doc_type)
    
    # limpa indices elasticsearch
    ep.to_es(df.iloc[50000:], index, doc_type=doc_type, _op_type='delete', thread_count=2, chunk_size=10000)
    # carrega dados elasticsearch
    ep.to_es(df, index, doc_type=doc_type, use_index=True)

    print("\n")

t1 = PythonOperator(
    task_id='streaming_desk', 
    python_callable=carrega_dados_desk,
    dag=dag
)

t1 