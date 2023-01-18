import re
import json
import time
import datetime
import requests
import lxml
from bs4 import BeautifulSoup
from fake_headers import Headers
from requests.auth import HTTPProxyAuth
from settings.config_db import DATABASE, USER, PASS, HOST
from settings.urls import url_cb, url_ali, url_ali_alt
from settings.other_data import PROXY_LIST, PRICE_LOG, CONNECTION_LOG, DB_ADDITION_LOG
from sqlalchemy import create_engine, Table, MetaData


def write_log(file_name, ex) -> None:
    with open(file_name, 'a') as file:
        file.write(str(ex))


def get_proxies(file) -> str:
    with open(file, 'r') as file:
        data = json.load(file)
        for i in data:
            ip = tuple(i.keys())[0]
            logipass = tuple(i[ip].items())[0]
            yield ((ip,) + logipass)


def get_alternate_ali(url):
    fake_header = Headers(os="mac", headers=True).generate()
    response = requests.get(url=url, headers=fake_header)
    soup = BeautifulSoup(response.text, 'lxml')
    third_td = soup.select("table tr:nth-child(2) td:nth-child(3)")
    text = third_td[0].text
    return float(text)


def scrap_data(url_ali) -> str:
    try:
        headers = Headers(os="mac", headers=True).generate()
        data = get_proxies(PROXY_LIST)
        ip, login, password = next(data, (None, None, None))
        if ip and login and password:
            proxies = {'http': f'http://{ip}'}
            auth = HTTPProxyAuth(login, password)
            response = requests.get(url=url_ali, headers=headers, proxies=proxies, auth=auth)
        else:
            response = requests.get(url=url_ali, headers=headers)

        soup = BeautifulSoup(response.text, 'lxml')
        data = soup.find('div', 'snow-price_SnowPrice__mainS__18x8np')
        if isinstance(data):
            return data.text
        else:
            get_alternate_ali(url_ali_alt)
    except Exception as ex:
        write_log(CONNECTION_LOG, ex)


def get_ali_currency(url_ali) -> float:
    while True:
        try:
            price = scrap_data(url_ali)
            price = float(re.sub(r'[^\d,]', '', price).replace(',', '.'))
            return price
        except Exception as ex:
            write_log(PRICE_LOG, ex)


def get_cb_currency(url) -> float:
    while True:
        try:
            response = requests.get(url=url)
            soup = BeautifulSoup(response.text, 'lxml')
            cb_data = soup.find_all('tr')
            for td in cb_data:
                if 'USD' in td.text:
                    return round(float(td.text.split()[-1].replace(',', '.')), 2)
        except Exception as ex:
            write_log(CONNECTION_LOG, ex)
            time.sleep(10)


def check_internet_connection(timeout=3) -> bool:
    try:
        return requests.get("http://httpbin.org/", timeout=timeout).status_code == 200
    except requests.ConnectionError as ex:
        write_log(CONNECTION_LOG, ex)


def insert_data(USER, PASS, HOST, DATABASE, ali, cb) -> None:
    # information about the database
    meta = MetaData()

    # db_connection
    engine = create_engine(f'mysql+mysqlconnector://{USER}:{PASS}@{HOST}/{DATABASE}', echo=False)
    meta.create_all(engine)
    currency = Table('currency', meta, autoload=True, autoload_with=engine)
    conn = engine.connect()

    db_append_data = currency.insert().values(ali=ali, cb=cb, currency_difference=ali - cb)
    conn.execute(db_append_data)
    with open(DB_ADDITION_LOG, 'a') as file:
        file.write(f'Success: {datetime.datetime.now()}\n')


def main() -> None:
    while True:
        if check_internet_connection():
            ali = get_ali_currency(url_ali)
            cb = get_cb_currency(url_cb)
            insert_data(USER, PASS, HOST, DATABASE, ali, cb)
            break


if __name__ == '__main__':
    main()
