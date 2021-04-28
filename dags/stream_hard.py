# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 13:31:57 2021
@author: Clecio Antao
Rotina para leitura de dados hardware para SQL e Streaming
"""

from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.email_operator import EmailOperator
#from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago

dag = DAG(
    "streaming_hard",
    default_args={
        "owner": "airflow",
        'email': ['clecio.antao@gmail.com'],
        'email_on_failure': True,
    },
    schedule_interval='* * * * *',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=4),
    tags=['etl'],
)

def carrega_dados_hard():

    from datetime import datetime
    import pandas as pd
    import psutil
    import sqlalchemy
    import time
    from es_pandas import es_pandas
   
    def main():

        print('entrou no main')

        # dataabase connection - assign to the correct values
        engineorigem = sqlalchemy.create_engine('mssql+pyodbc://sa:Proteu690201@192.168.2.120/bi_integracao?driver=SQL Server')
        #engineorigem = sqlalchemy.create_engine('mssql+pyodbc://sa:Proteu690201@127.0.0.1/metrics?driver=SQL Server')
        
        # gets the disk partitions in order to get a list of NFTS drives
        drps = psutil.disk_partitions()
        drives = [dp.device for dp in drps if dp.fstype == 'NTFS']
        
        # initialises the data frame with the appropriate values
        df = pd.DataFrame(
            {
                'CPU_usada': int(get_cpu_usage_pct()),
                'CPU_frequencia': int(get_cpu_frequency()),
                'RAM_total': get_ram_total() // 1024 // 1024,
                'RAM_utilizada': int(round(get_ram_usage() / 1024 // 1024)),
                'RAM_utilizada%': round(get_ram_usage_pct()),
                #'MEM_virtual': [psutil.virtual_memory()[2]],
                'UltimoBoot' : datetime.fromtimestamp(psutil.boot_time()).strftime('%d-%m-%Y %H:%M:%S')
            }, 
                index=[0] 
            )
        
        print(df['CPU_usada'])
        
        # records the drive usage for each drive found
        for drive in drives:
            df['{}_Driver_uso'.format(drive.replace(":\\",""))] = psutil.disk_usage(drive)[3]
            
        # adds the current date and time stamp      
        df['DataRegistro'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        #df['RAM_utilizada%'] = 100
        
        #if_exists="replace" if the table does not yet exist, then add HistoryID (or ID) as the auto-incremented primary key
        df.to_sql(name='cpu_mem_disco', con=engineorigem, if_exists='append', index=False)
        
        # Dados Elasticsearch
        es_host = '192.168.2.120:9200'
        index = 'cpu_mem_disco'

        # Cria instancia es_pandas 
        ep = es_pandas(es_host)
        
        # init template if you want
        doc_type = 'cpu_mem_disco'
        ep.init_es_tmpl(df, doc_type)
    
        # limpa indices elasticsearch
        #ep.to_es(df.iloc[50000:], index, doc_type=doc_type, _op_type='delete', thread_count=2, chunk_size=10000)
        # carrega dados elasticsearch
        #ep.to_es(df, index, doc_type=doc_type, use_index=True)
        ep.to_es(df, index, doc_type=doc_type, thread_count=2, chunk_size=10000)
        
    def get_cpu_usage_pct():
        """
        Obtains the system's average CPU load as measured over a period of 500 milliseconds.
        :returns: System CPU load as a percentage.
        :rtype: float
        """
        return psutil.cpu_percent(interval=0.5)
       
    def get_cpu_frequency():
        """
        Obtains the real-time value of the current CPU frequency.
        :returns: Current CPU frequency in MHz.
        :rtype: int
        """
        return int(psutil.cpu_freq().current)
    
    def get_ram_usage():
        """
        Obtains the absolute number of RAM bytes currently in use by the system.
        :returns: System RAM usage in bytes.
        :rtype: int
        """
        return int(psutil.virtual_memory().total - psutil.virtual_memory().available)
    
    def get_ram_total():
        """
        Obtains the total amount of RAM in bytes available to the system.
        :returns: Total system RAM in bytes.
        :rtype: int
        """
        return int(psutil.virtual_memory().total)
    
    def get_ram_usage_pct():
        """
        Obtains the system's current RAM usage.
        :returns: System RAM usage as a percentage.
        :rtype: float
        """
        return psutil.virtual_memory().percent
    
    def get_swap_usage():
        """
        Obtains the absolute number of Swap bytes currently in use by the system.
        :returns: System Swap usage in bytes.
        :rtype: int
        """
        return int(psutil.swap_memory().used)
    
    def get_swap_total():
        """
        Obtains the total amount of Swap in bytes available to the system.
        :returns: Total system Swap in bytes.
        :rtype: int
        """
        return int(psutil.swap_memory().total)
    
    def get_swap_usage_pct():
        """
        Obtains the system's current Swap usage.
        :returns: System Swap usage as a percentage.
        :rtype: float
        """
        return psutil.swap_memory().percent
                
    #time.sleep(1)

    print('Execução completa!')

t1 = PythonOperator(
    task_id='streaming_hard', 
    python_callable=carrega_dados_hard,
    dag=dag
)

t1 