from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import os
import time
import requests


# Меняем количество страниц и ссылку поиска
executable_path = r"chromedriver.exe"
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_experimental_option('w3c', True)

browser = webdriver.Chrome(executable_path=executable_path, options=chrome_options)
list_zakupki = []
for page in range(1, 2):
    browser.get('https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=%D0%94%D0%B5%D0%BF%D0%B0%D1%80%D1%82%D0%B0%D0%BC%D0%B5%D0%BD%D1%82+%D0%98%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%BD%D1%8B%D1%85+%D0%A2%D0%B5%D1%85%D0%BD%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D0%B9+%D0%9E%D1%80%D0%BB%D0%BE%D0%B2%D1%81%D0%BA%D0%BE%D0%B9+%D0%BE%D0%B1%D0%BB%D0%B0%D1%81%D1%82%D0%B8&morphology=on&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&'
                'pageNumber={}'
                '&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on&af=on&ca=on&pc=on&currencyIdGeneral=-1'
                .format(page))
    source_html = BeautifulSoup(browser.page_source, "html.parser")
    for content in source_html.find_all('div', class_='registry-entry__header-mid__number'):
        number_zakupki = ' '.join(content.contents[1].text.split()).split('№')[1]
        list_zakupki.append(number_zakupki[1:])

print(list_zakupki)
# list_zakupki =

# По каждой закупке идем
for number in list_zakupki:
    browser.get('https://zakupki.gov.ru/epz/order/notice/ea44/view/supplier-results.html?regNumber={}'.format(number))
    time.sleep(1)
    zakupka_html = BeautifulSoup(browser.page_source, "html.parser")

    # Берем инфу о закупке
    description = ' '.join(zakupka_html.find_all('span', class_='cardMainInfo__content')[0].text.split())
    start_price = ' '.join(zakupka_html.find('span', class_='cardMainInfo__content cost').text.split())
    start_time = ' '.join(zakupka_html.find_all('span', class_='cardMainInfo__content')[3].text.split())
    try:
        end_time = ' '.join(zakupka_html.find_all('span', class_='cardMainInfo__content')[5].text.split())
    except IndexError:
        end_time = 'Нет инфоромации'

    # Создаем папку с номером закупки
    try:
        zakupka_path = './result/dit/{}/{}'.format(start_time.split('.')[2], number)
        os.mkdir(zakupka_path)
    except FileExistsError:
        pass

    try:
        browser.find_element_by_class_name('chevronRight.draftArrow').click()
        time.sleep(1)
        zakupka_html = BeautifulSoup(browser.page_source, "html.parser")

        # Парсим участников
        zakupki_member = ""
        table = zakupka_html.find_all('table', class_='blockInfo__table tableBlock')
        for row in table[1].contents[3].contents:
            try:
                name_member = ' '.join(row.contents[1].text.split())
                price_member = ' '.join(row.contents[5].text.split())
                info_zakupki_member = "{} - {}".format(name_member, price_member)
                zakupki_member = "{}\n {}\n".format(zakupki_member, info_zakupki_member)
            except:
                pass

        # Выкачиваем контракт
        contract_href = \
        zakupka_html.find('span', class_='icon icon-small icon-cryptoSign_small vAlignMiddle').parent.parent.contents[
            5].contents[1].attrs['href']
        executable_path = r"chromedriver.exe"
        download_options = Options()
        # download_options.add_argument('--headless')
        # download_options.add_argument('--no-sandbox')
        download_options.add_experimental_option("prefs", {
            "download.default_directory": r"d:\Ucheba\fourthsem\Sorokin\pythonProjects\zakupki{}".format(
                zakupka_path[1:].replace(r'/', '\\')),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        download_browser = webdriver.Chrome(executable_path=executable_path, options=download_options)
        download_browser.get(contract_href)
        time.sleep(1)

    except NoSuchElementException:
        zakupki_member = ""


    # Создаем в нем инфу о компаниях и названии закупки
    with open('{}/Информация о закупке.txt'.format(zakupka_path), 'w', encoding="utf-8") as file:
        file.write("""
            Описание закупки: {} \n
            Начальная цена закупки: {} \n
            Время начала закупки: {} \n
            Время окончания закупки: {} \n
            \n
            Участники (первый победитель, через тире предложенная цена ): \n
            {}
        """.format(description, start_price, start_time, end_time, zakupki_member))
