from selenium import webdriver
from bs4 import BeautifulSoup

import json
import os
import re
import time
import wget
from datetime import datetime
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
import mysql.connector
from mysql.connector import Error


# Connect to BD
# —-------------------------------------------—
config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'russian_today',
    'raise_on_warnings': True
}

conn = mysql.connector.connect(**config)


def insert_row(query, data):
    try:
        cursor = conn.cursor()
        cursor.executemany(query, data)

        conn.commit()
    except Error as e:
        print('Error:', e)

    finally:
        cursor.close()


def get_head_info(html, count_on_load, id):
    div_news = html.find_all('div', class_="listing__card_all-news")

    # Проходим по все новостям на этой странице, забираем категорию, описание, заголовок, время и ссылку на статью
    news_info = list()
    categories_list = ['Россия', 'Мир', 'Экономика', 'Спорт', 'Наука']
    categories_eng = {'Россия': 'russia',
                      'Мир': 'world',
                      'Экономика': 'economics',
                      'Спорт': 'sport',
                      'Наука': 'science',
                      }

    for news in div_news[count_on_load:]:
        category = news.find('div', class_='card__category').text
        if category not in categories_list:
            category = 'Мир'
        heading = news.find('div', class_='card__heading').text
        url = news.find('div', class_='card__heading').find('a', class_='link').attrs['href']
        date = news.find('div', class_='card__date').text
        description = news.find('div', class_='card__summary').text
        news_info.append({
            'id': id,
            'url': 'https://russian.rt.com{}'.format(url),
            'category': categories_eng[category],
            'category_ru': category,
            'heading': heading,
            'article_date': date,
            'description': description,
        })
        id += 1
    print('Забрал {} статей'.format(count_on_load+len(news_info)))
    print(news_info)
    return news_info


def get_info_post(news_info, browser):
    post_info = []
    for news in news_info:
        browser.get(news['url'])
        source_html = BeautifulSoup(browser.page_source, "html.parser")
        try:
            images_url = source_html.find('img', class_='article__cover-image').attrs['src']
            src_photo = re.search(".*\/(.*)", images_url)
            path_src_photo = "news_img/" + src_photo[1]
            if not os.path.exists(path_src_photo):
                filename = wget.download(images_url)
                os.rename(filename, path_src_photo)
            news['path_src_photo'] = path_src_photo
            print('Забрали фоточку')
        except:
            news['path_src_photo'] = ''

        try:
            news['author'] = source_html.find('div', class_='article__author').text
        except:
            news['author'] = ""
        news['text'] = source_html.find('div', class_='article__text').text
        # with open('news.json', 'a', encoding='utf-8') as f:
        #     json.dump(news, f, ensure_ascii=False, indent=2)
        post_info.append(news)
    return post_info


def main_scrapper():
    executable_path = r"chromedriver.exe"
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')

    browser = webdriver.Chrome(executable_path=executable_path, options=chrome_options)
    browser.get('https://russian.rt.com/news')
    # browser.maximize_window()
    browser.find_element_by_link_text('Подтвердить').click()
    # подтверждаем куки и подписку
    browser.find_element_by_class_name('subscribe-layout')
    browser.find_element_by_class_name('subscribe__close').click()

    # Вытаскиваем все ссылки новостей с страницы и их категории и тд
    news_arr = list()
    count_on_load = 0
    while len(news_arr) < 15:
        id = count_on_load + 1
        source_html = BeautifulSoup(browser.page_source, "html.parser")
        news_arr += get_head_info(source_html, count_on_load, id)

        # Пролистываем страницу до конца (загружается js)
        next_button = browser.find_element_by_class_name('button__item')
        browser.execute_script("arguments[0].scrollIntoView(false);", next_button)

        # Тыкаем на загрузку следующих новостей
        print('Загрузили некст')
        next_button.click()
        time.sleep(1)
        count_on_load += 15

    post_info = get_info_post(news_arr, browser)

    return post_info




def to_database(arr):
    query = 'INSERT INTO articles(id, url, author, category,  category_ru, heading, article_date, description, path_src_photo, text) ' \
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,  %s) ' \
            'ON DUPLICATE KEY UPDATE id=VALUES(id), url=VALUES(url), author=VALUES(author),category=VALUES(category), category_ru=VALUES(category_ru),' \
            'heading=VALUES(heading), article_date=VALUES(article_date), description=VALUES(description), ' \
            'path_src_photo=VALUES(path_src_photo), text= VALUES(text)'

    articles_info = []
    for article in arr:
        info = [article['id'], article['url'], article['author'],  article['category'], article['category_ru'], article['heading'],
                article['article_date'], article['description'], article['path_src_photo'], article['text']]
        articles_info.append(info)

    insert_row(query, articles_info)
