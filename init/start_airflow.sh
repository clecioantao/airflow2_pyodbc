#!/usr/bin/env bash

echo "Executing start_airflow.sh"

/usr/local/bin/python -m pip install --upgrade pip
pip install -r /opt/airflow/init/requirements.txt

echo "Starting scheduler"
airflow scheduler &
echo "Starting webserver"
airflow webserver
