# VERSION 2.0.1
# AUTHOR: Clecio Antao
# DESCRIPTION: Imagem Airflow 2.0.1 with PyODBC
# BUILD: docker build -t clecio/airflow_pyodbc:1.10.9 .
# SOURCE: 

FROM apache/airflow:2.0.1

USER root

ENV ACCEPT_EULA=Y

RUN apt-get update && apt-get install -y \
    gnupg2 \
    curl apt-transport-https debconf-utils && \
    echo "deb http://deb.debian.org/debian jessie main" >> /etc/apt/sources.list && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/8/prod.list > /etc/apt/sources.list.d/mssql-release.list 
    
RUN apt-get update && \
    apt-get install -y \
        libcurl3 \
        msodbcsql \
        mssql-tools \
        unixodbc-dev \
        libssl1.0.0 
        
RUN apt-get install -y --reinstall --upgrade \
        g++ \
        gcc && \
    /bin/bash -c "source ~/.bashrc" 
RUN pip install --upgrade \
        six \
        pyodbc \
        es_pandas \
        progressbar \
        progressbar2 \
        pip install psutil \
        pip install 'apache-airflow-providers-microsoft-mssql' \
        psycopg2-binary && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean 
   
USER airflow

RUN pip install fabric3==1.14.post1 flask_bcrypt==0.7.1 slackclient==1.3.1 boto3==1.9.143 xlrd==1.2.0 hvac==0.6.4 flatten_json==0.1.6 --user

ENV PATH="$PATH:/opt/mssql-tools/bin:/usr/local/airflow/.local/bin"