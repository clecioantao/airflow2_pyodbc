from airflow import DAG
from airflow.contrib.operators.dataproc_operator import DataProcPySparkOperator


def weekday_subdag(
    parent_dag=None, 
    task_id=None, 
    schedule_interval=None, 
    default_args=None
):

    subdag = DAG(
        f"{parent_dag}.{task_id}",
        schedule_interval=schedule_interval,
        default_args=default_args,
    )

    pyspark_jobs = ["avg_speed", "avg_temperature", "avg_tire_pressure"]

    for job in pyspark_jobs:

        DataProcPySparkOperator(
            task_id=f"{job}",
            main=f"gs://ca-logistics-spark-bucket/pyspark/weekday/{job}.py",
            cluster_name="spark-cluster-{{ ts_nodash }}",
            dataproc_pyspark_jars="spark-lib/bigquery/spark-bigquery-latest_2.12.jar",
            dag=subdag,
        )

    return subdag