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
    "trata_relatorios",
    default_args={
        "owner": "airflow",
        'email': ['clecio.antao@gmail.com'],
        'email_on_failure': True,
    },
    schedule_interval='0 */2 * * *',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=4),
    tags=['etl'],
)

def carrega_dados():

    import pandas as pd
    import requests
    import json
    import sqlalchemy
            
    # CRIA ENGINE DE ORIGEM - CONNECT SQL SERVER

    engineorigem = sqlalchemy.create_engine('mssql+pyodbc://sa:Proteu690201@192.168.2.90/deskmanager?driver=ODBC+Driver+17+for+SQL+Server')
        
    # AUTENTICAÇÃO API
    url = "https://api.desk.ms/Login/autenticar"
    pubkey = '\"ef89a6460dbd71f2e37a999514d2543b99509d4f\"'
    payload=" {\r\n  \"PublicKey\" :" + pubkey + "\r\n}"
    headers = {
    'Authorization': '66e22b87364fa2946f2ce04dce1b8b59b669ab7f',
    'Content-Type': 'application/json'
    }
    token = requests.request("POST", url, headers=headers, data=payload)
    resp_token = json.loads(token.text)
    
    print('Token: ', resp_token)

    # ENTRA NA API PARA BUSCAR NUMERO DE COLUNAS
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
    colunas = len(df.columns)
    ############################

    relatorios_pag = 0
    paginas = 5000 
    contador = 1
    tabela = 'chamados_streaming' ## nome da tabela que sera criada ou sobreposta
    
    while contador >= 1:

        print('Paginas: ', paginas)
        print('Contador: ', contador)
        print('Linhas: ',relatorios_pag)
        
        #################################
        # LISTA DE relatorios - paginação de 5000 em 5000 
        url = "https://api.desk.ms/Relatorios/imprimir"
        paginador = '\"' +  str(relatorios_pag) + '\"'
        payload="{\r\n  \"Chave\" :"  + relatorio +  ", \r\n  \"APartirDe\" :" + paginador + ", \r\n  \"Total\": \"\" \r\n}"
        headers = {
        'Authorization': resp_token,
        'Content-Type': 'application/json'
        }
        resp = requests.request("POST", url, headers=headers, data=payload)
        resp_data = json.loads(resp.text)
        root = resp_data['root']
        df = pd.DataFrame(root)
    
        # EXPORTANDO DADASET PARA TABELA BANCO SQL SERVER
        # CALCULA O CHUNKSIZE MÁXIMO E VERIFICA FINAL LINHAS
        if len(df.columns) == colunas:
            cs = 2097 // len(df.columns)  # duas barras faz a divisão e tras numero inteiro
            if cs > 1000:
                cs = 1000
            else:
                cs = cs
        else:
            break
        
        # INSERE DADOS TABELA SQL SEVER
        if relatorios_pag == 0:
            df.to_sql(name=tabela, con=engineorigem, if_exists='replace', chunksize=cs)
        else:
            df.to_sql(name=tabela, con=engineorigem, if_exists='append', chunksize=cs)
            
        relatorios_pag = relatorios_pag + 5000
        contador =  contador + 1

t1 = PythonOperator(
    task_id='popula_relatorios', 
    python_callable=carrega_dados,
    dag=dag
)

t1 