import re

from bs4 import BeautifulSoup
from json import dumps, load, loads
from pprint import pprint


def read_from_stream(file_name, data_type=None):
    data={}
    with open("/opt/airflow/dags/data/"+file_name, "r") as f:
        if data_type == 'json':
            data = load(f)

    return data


def write_to_stream(data, file_name=None, data_type=None, append=None):
    if file_name:
        if append:
            f = open("/opt/airflow/dags/data/"+file_name, "a")
        else:
            f = open("/opt/airflow/dags/data/"+file_name, "w")

        if data_type == 'html':
            soup = BeautifulSoup(data, features='html5lib')
            f.write(data.prettify())
        elif data_type == 'json':
            f.write(dumps(data, indent=2))
        else:
            f.write(data)

        f.close()
    else:
        if data_type == 'html':
            print(data.prettify())
        elif data_type == 'json':
            pprint(data)
        else:
            print(data)


def process_financials_data():
    ret_dictionary={}

    def process_time_series(store):
        for key in store['timeSeries']:
            if len(store['timeSeries'][key]):
                for entry in store['timeSeries'][key]:
                    if type(entry) == type({}) and len(entry):
                        # print(f"{store['meta']['symbol']},{entry['asOfDate']},{entry['periodType']},{key},{entry['reportedValue']},'timeSeries'")
                        if key in ret_dictionary.keys():
                            if entry['asOfDate'] in ret_dictionary[key].keys():
                                ret_dictionary[key][entry['asOfDate']][entry['periodType']] = entry['reportedValue']['raw']
                            else:
                                ret_dictionary[key][entry['asOfDate']] = {entry['periodType'] : entry['reportedValue']['raw']}
                        else:
                            ret_dictionary[key] = {entry['asOfDate']:{entry['periodType'] : entry['reportedValue']['raw']}}


    def process_subsection(store, section1, section2, tag):
        for item in store[section1][section2]:
            for entry in item:
                if entry in ['endDate', 'maxAge']:
                    pass
                elif len(item[entry]):
                    # print(f"{store['symbol']},{item['endDate']['fmt']},{tag},{entry},{item[entry]},'{section1}:{section2}'")
                    if entry in ret_dictionary.keys():
                        if item['endDate']['fmt'] in ret_dictionary[entry].keys():
                            ret_dictionary[entry][item['endDate']['fmt']][tag] = item[entry]['raw']
                        else:
                            ret_dictionary[entry][item['endDate']['fmt']] = {tag : item[entry]['raw']}
                    else:
                        ret_dictionary[entry] = {item['endDate']['fmt'] : {tag : item[entry]['raw']}}


    html_text = open('/opt/airflow/dags/data/in.txt', 'r').read()
    soup = BeautifulSoup(html_text, features='html5lib')
    script = soup.find("script",text=re.compile("root.App.main")).text
    data = loads(re.search("root.App.main\s+=\s+(\{.*\})", script).group(1))
    store = data["context"]["dispatcher"]["stores"]

    ret_dictionary['symbol'] = store['QuoteSummaryStore']['price']['symbol']
    process_time_series(store['QuoteTimeSeriesStore'])
    process_subsection(store['QuoteSummaryStore'], 'balanceSheetHistory', 'balanceSheetStatements', "12M")
    process_subsection(store['QuoteSummaryStore'], 'balanceSheetHistoryQuarterly', 'balanceSheetStatements', "3M")
    process_subsection(store['QuoteSummaryStore'], 'cashflowStatementHistory', 'cashflowStatements', "12M")
    process_subsection(store['QuoteSummaryStore'], 'cashflowStatementHistoryQuarterly', 'cashflowStatements', "3M")
    process_subsection(store['QuoteSummaryStore'], 'incomeStatementHistory', 'incomeStatementHistory', "12M")
    process_subsection(store['QuoteSummaryStore'], 'incomeStatementHistoryQuarterly', 'incomeStatementHistory', "3M")

    return ret_dictionary
