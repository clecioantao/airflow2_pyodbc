import os
from utils.parser import process_financials_data, write_to_stream


def _check_for_content():
    is_empty = os.stat('/opt/airflow/dags/data/in.txt').st_size == 0
    if is_empty:
        return 'print_no_data'
    else:
        return 'process_data'

def _process_data(**context):
    task_instance = context['ti']
    ret = process_financials_data()
    task_instance.xcom_push('ret', ret)
    return ret

def _store_data(**context):
    task_instance = context['ti']
    ret = task_instance.xcom_pull(task_ids='process_data', key='ret')
    write_to_stream(ret, data_type='json', file_name='out.txt')

    return_value = ''
    ticker = ret['symbol']

    for entry in ret.keys():
        if entry != 'symbol':
            metric = entry
            for date in ret[entry].keys():
                record_date = date
                timeframe = list(ret[entry][date].keys())[0]
                value = list(ret[entry][date].values())[0]
                if len(return_value): return_value += ','
                return_value += f'''('{ticker}','{record_date}','{timeframe}','{metric}',{value})'''

    task_instance.xcom_push('return_value', return_value)
    return return_value


    return True
