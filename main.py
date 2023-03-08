from datetime import datetime
import os
import csv
import time

import requests
import fake_useragent
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.firefox.webdriver import WebDriver
from dotenv import load_dotenv

load_dotenv()

base_dir = os.getcwd()
filename = str(datetime.now())
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0', 'accept': '*/*'}
session = requests.Session()
HOST = 'https://store.konecranes.com'
fake_user = fake_useragent.UserAgent().random
header = {
    'user-agent': fake_user
}


def wait_to_load_page(driver: WebDriver) -> None:
    WebDriverWait(driver, 15).until(ec.presence_of_element_located((By.TAG_NAME, "html")))
    time.sleep(0.1)


def autorization() -> WebDriver:
    if os.getenv("system") == 'windows': 
        DRIVER= base_dir + "/geckodriver.exe"
        service = Service(executable_path=DRIVER)
        options = webdriver.FirefoxOptions()
        options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
        options.add_argument(('--headless'))
        driver = webdriver.Firefox(service=service, options=options)
    elif os.getenv("system") == 'linux': 
        DRIVER="geckodriver"
        service = Service(executable_path=DRIVER)
        options = webdriver.FirefoxOptions()
        options.add_argument('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0')
        options.add_argument(('--headless'))
        driver = webdriver.Firefox(service=service, options=options)
    else:
        print("Укажите операционную систему в файле .env")
        exit()

    driver.get('https://store.konecranes.com/cpc/en/BRAKE-DISC-SET/p?p=c66rYesZ4CC9O4cOd17ZNA%3D%3D_52314611')
    wait_to_load_page(driver)
    driver.find_element(By.XPATH, '/html/body/main/header/nav[2]/div/div/div[4]/div/div/div/ul/li/a').click()
    time.sleep(3)

    email_input = driver.find_element(By.XPATH, '//*[@id="1-email"]')
    email_input.clear()
    email_input.send_keys(os.getenv("mail"))
    password_input = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div[3]/div/div/form/div/div/div/div/div[2]/div[2]/span/div/div/div/div/div/div/div/div/div/div/div[2]/div/div/input')
    password_input.clear()
    password_input.send_keys(os.getenv("password"))
    driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div/div[3]/div/div/form/div/div/div/button/span').click()
    wait_to_load_page(driver)
    return driver


def get_html(url: str, params: dict=None) -> requests.models.Response:
    r = requests.get(url, headers=header, params=params)
    return r


def driver_get_page(url: str, driver: WebDriver) -> WebDriver:
    return driver.get(url)


def get_pages_count_and_name(html: str) -> int and str or int and None:
    soup = BeautifulSoup(html, 'html.parser')
    try:
        paginationTo = soup.find('ul', class_='pagination')
        pagination = paginationTo.find_all('a')
        pages_count = int(pagination[-2].get_text())  
        pagination_pre_name = pagination[-2].get('href')
        pagination_name = pagination_pre_name[pagination_pre_name.rfind('?'):pagination_pre_name.rfind('page')+4]
        return pages_count, pagination_name
    except:
        return 1, None
                    

def get_content(url: str, driver: WebDriver) -> list:
    driver_get_page(url, driver)
    wait_to_load_page(driver)
    html_from_selenium = driver.page_source
    soup = BeautifulSoup(html_from_selenium, 'html.parser')

    products_card = soup.find_all('div', class_='product__list-details')
    catalog_list = []
    for product in products_card:
        try:
            more_product_info = HOST + product.find('a').get('href')
        except:
            continue

        driver_get_page(more_product_info, driver)
        wait_to_load_page(driver)
        
        html_product_from_selenium = driver.page_source
        soup = BeautifulSoup(html_product_from_selenium, 'html.parser')

        try:
            price = soup.find('div', class_='netprice').get_text(strip=True)[2:-4].replace(',', '')
        except:
            price = None
        
        try:
            short_text = soup.find('div', class_='short-sales-text').get_text(strip=True)
        except:
            short_text = None
        
        try:
            kcid = soup.find('div', class_='product-kcid').get_text(strip=True)[6:]
        except:
            kcid = None

        try:
            img_href = HOST + soup.find('div', class_='gallery-top').find('img')['src']
        except:
            img_href = None

        try:
            code = HOST + soup.find('span', class_='code').get_text(strip=True)
        except:
            code = None

        try:
            name = HOST + soup.find('h1', class_='page-headline').get_text(strip=True)
        except:
            name = None
        
        table = soup.find('table', class_='vertical-table')
        table_data = table.find_all('tr')
        specification, weight, customs_code = None, None, None
        for data in table_data:
            pre_data = data.get_text(strip=True)
            if 'Specification' in pre_data:
                specification = pre_data[13:]
            if 'Weight' in pre_data:
                weight = pre_data[6:]
            if 'Customs code:' in pre_data:
                customs_code = pre_data[13:]

        catalog_list.append({
            'Name': name,
            'Code': code,
            'Short': short_text,
            'KCID': kcid,
            'Specification': specification,
            'Weight': weight,
            'Customs code:': customs_code,
            'Price': price,
            'Pic': img_href
        })
    return catalog_list


def create_file(path: str) -> None:
    with open(path, 'w',  encoding='utf8', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(['Name', 'Code', 'Short', 'KCID', 'Specification', 'Weight', 'Customs code:', 'Price', 'Pic'])


def append_to_file(items: dict, path: str) -> None:
    with open(path, 'a',  encoding='utf8', newline='') as file:
        writer = csv.writer(file, delimiter=',')
        for item in items:
            writer.writerow([item['Name'], item['Code'], item['Short'], item['KCID'], item['Specification'], item['Weight'], item['Customs code:'], item['Price'], item['Pic']])


def url_list() -> list:
    url_clean_list = []
    url_list_dir = base_dir + '/' + os.getenv("dir_url_name") + '/'
    for file in os.listdir(url_list_dir):
        with open((os.path.join(url_list_dir, file))) as urls:
            url_dirt_list = urls.read().split('\n')
            for url in url_dirt_list:
                if 'https' in url:
                    url_clean_list.append(url[url.find("https"):])
    return url_clean_list


def get_data_from_single_page(URL: str, final_data_list: list, driver: WebDriver) -> list:
    print(f'Парсинг страницы {URL}...')
    final_data_list.extend(get_content(URL, driver))
    wait_to_load_page(driver)
    return final_data_list 


def get_data_from_many_pages(URL: str, final_data_list: list, pages_count: int, pagination_name: str, driver: WebDriver) -> list:
    for number_page in range (0, pages_count):
        print(f'Парсинг страницы {number_page +1} {pages_count} {URL}...')
        if '?text' in URL:
            URL = URL[:URL.find('?text')]
        Page = f'{URL}{pagination_name}={str(number_page)}'
        final_data_list.extend(get_content(Page, driver))
        wait_to_load_page(driver)
    return final_data_list 


def parse() -> None:
    FILE = base_dir + '/' + os.getenv("dir_result_name") + '/' + filename.replace(':', ';') + '.csv'
    create_file(FILE)
    driver = autorization()
    for URL in url_list():
        html_request = get_html(URL)
        final_data_list = []
        pages_count, pagination_name = get_pages_count_and_name(html_request.text)
        if pages_count == 1:
            get_data_from_single_page(URL, final_data_list, driver)
        else:
            get_data_from_many_pages(URL, final_data_list, pages_count, pagination_name, driver)  
        append_to_file(final_data_list, FILE)
        print(f'Получено {len(final_data_list)} товаров')
    driver.quit()

parse()
