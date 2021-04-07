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
    schedule_interval='*/50 * * * *',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=4),
    tags=['etl'],
)

def carrega_dados():

    import pandas as pd
    import requests
    import json
    import sqlalchemy
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime
            
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
    
    # VERIFICA QUANTIDADE DE REGISTROS
    url = "https://api.desk.ms/Relatorios/imprimir"
    paginador = '\"' +  ' ' + '\"'
    relatorio = "857"
    payload="{\r\n  \"Chave\":\"857\", \r\n  \"APartirDe\":\"\", \r\n  \"Total\":\"\"\r\n}"
    #payload="{\r\n  \"Chave\" :"  + relatorio +  ", \r\n  \"APartirDe\" : \" " + paginador + ", \r\n  \"Total\": \"\" \r\n}"
    headers = {
      'Authorization': resp_token,
      'Content-Type': 'application/json'
    }
    resp = requests.request("POST", url, headers=headers, data=payload)
    resp_data = json.loads(resp.text)
    root = resp_data['root']
    df = pd.DataFrame(root)
    index = df.index
    total_linhas = len(index)
    print('Total de linhas: ', total_linhas)
    
    # CRIAR LAÇO 
    print(resp_token)
    
    #relatorios_total =  100000
    relatorios_pag = 0
    paginas = 100000 #round((relatorios_total / 5000) + 0.5)
    contador = 1
    tabela = 'total_geral'
      
    while contador <= paginas:
        print('entrou no laço')
        print('Paginas: ', paginas)
        print('Contador: ', contador)
        print('Linhas: ',relatorios_pag)
        print('Colunas: ',len(df.columns))
        #################################
        # LISTA DE relatorios - paginação de 3000 em 3000 
        url = "https://api.desk.ms/Relatorios/imprimir"
        paginador = '\"' +  str(relatorios_pag) + '\"'
        relatorio = "857"
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
        if len(df.columns):
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