from pdf_parser import pdf_parser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import exceptions
import re
from urllib.request import urlretrieve
import json
import os
from pprint import pprint

def scrapping_arxiv_on_request(search_phrase, count_of_articles=10):
    """
    :param search_phrase: поисковая фраза
    :param count_of_articles: количество статей, которые будут просмотрены
    :return: спиок информациии о статьях
    """
    # Активация селениума
    browser = webdriver.Chrome(executable_path=r"D:\Ucheba\fourthsem\Sorokin\pythonProjects\arxiv\chromedriver.exe")
    browser.get("https://arxiv.org/")
    browser.find_element_by_class_name("keyword-field").send_keys(search_phrase)
    browser.find_element_by_class_name("btn-search-arxiv").click()
    node_article = []
    # Идем по странично и собираем данные о статьях, пока не перестанет показываться кнока "next" на странице
    # Либо запрошенное количество не превысило запрашиваемое
    number_of_result = 0
    while number_of_result != count_of_articles:
        html_search_result = BeautifulSoup(browser.page_source, "html.parser")
        # Проходим по каждой статье
        for article in html_search_result.find_all('li', {"class": "arxiv-result"}):
            if number_of_result != count_of_articles:
                # Забираем название
                name = re.sub(r"\n|\s{2,}", "", article.contents[3].text)
                try:
                    # Если есть - забираем doi
                    doi = article.contents[1].contents[3].contents[1].contents[1].contents[3].text
                except IndexError:
                    doi = ""
                # Забираем имя автора
                authors = re.sub(r"\s{2,}", "", article.contents[5].text[9:])
                authors = re.sub(r"\n(.*)\n", "\\1", authors).split(",")
                # Забираем дату
                date = re.sub(r"\n|\s{2,}", "", article.contents[9].contents[3])
                # Забираем теги
                subjects = []
                for key in range(1, len(article.contents[1].contents[3].contents), 2):
                    subjects.append(article.contents[1].contents[3].contents[key].attrs["data-tooltip"])
                # Добавлем links для нужной структуры
                links = []
                node_article.append([name, doi, authors, date, subjects, links])
                # Выгружаем статью, при этом из названия удаляем запрещенные символы
                path = "articles/"+search_phrase
                if not os.path.exists(path):
                    os.makedirs(path)
                try:
                    path_article = path+"/"+re.sub(r"[.%#&{}\\\/<>*?$!`:@+|=\"\']", "", name[:40])+'.pdf'
                    if not os.path.exists(path_article):
                        urlretrieve(article.contents[1].contents[1].contents[2].contents[1].attrs["href"]+".pdf", path_article)
                except IndexError:
                    continue
                number_of_result += 1
            else:
                break
        if number_of_result != count_of_articles:
            try:
                browser.find_element_by_class_name("pagination-next").click()
            except exceptions.NoSuchElementException:
                print("Exception, a lot of count_of_search, search result dont have so value")
                break
    browser.close()
    return node_article

def get_children_keywords(keywords_list):
   index = 1
   info_keyword = []
   for node in keywords_list:
       authors = []
       for person in node[2]:
           author = {
               "name": person,
               "size": 10,
           }
           authors.append(author)
       child = {
           "name": index,
           "name_article": node[0],
           "doi": node[1],
           "date": node[3],
           "subject": node[4],
           "links": node[5],
           "children": authors,
           "size": len(authors) * 10,
       }
       info_keyword.append(child)
       index += 1
   return info_keyword



def create_json(search_result, request):
    """
    :param search_result: итоговый список информации о всех нужных статьях
    :param request: фраза поиска
    :return: json файл нужного формата
    """
    children = []
    index = 1
    # Сначал формируем нужный формат для главной фразы поиска
    for node in search_result[0][request]:
        authors = []
        for person in node[2]:
            author = {
                "name": person,
                "size": 10,
            }
            authors.append(author)
        child = {
            "name": index,
            "name_article": node[0],
            "doi": node[1],
            "date": node[3],
            "subject": node[4],
            "links": node[5],
            "children": authors,
            "size": len(authors) * 10,
        }
        # Добавляем статьи в итоговый список
        children.append(child)
        index += 1
    children_keyword_first = []
    # Формируем нужный формат для клчевых слов
    for keyword_first in search_result[1]["keywords"]:
            children_keyword_second = []
            try:
                for keyword_second in search_result[1]["keywords"][keyword_first][-1]["keywords"]:
                    children_keyword_third = []
                    for keyword_third in search_result[1]["keywords"][keyword_first][-1]["keywords"][keyword_second][-1]["keywords"]:
                        children_keyword_third.append({
                            "name": keyword_third,
                            "size": 40,
                            "children": get_children_keywords(search_result[1]["keywords"][keyword_first][-1]["keywords"][keyword_second][-1]["keywords"][keyword_third]),
                        })
                    list_second_children = get_children_keywords(search_result[1]["keywords"][keyword_first][-1]["keywords"][keyword_second][:-1])
                    list_second_children.append({
                                    "name": "keywords",
                                    "size": 40,
                                    "children": children_keyword_third,
                                })
                    children_keyword_second.append({
                            "name": keyword_second,
                            "size": 40,
                            "children": list_second_children,
                        })
            except:
                pass
            list_first_children = get_children_keywords(search_result[1]["keywords"][keyword_first][:-1])
            list_first_children.append({
                        "name": "keywords",
                        "size": 40,
                        "children":  children_keyword_second,
                    })
            children_keyword_first.append({
                "name": keyword_first,
                "size": 40,
                "children": list_first_children,
            })
    # Добавляем ключевые слова в итоговый список
    children.append({
        "name": "keywords",
        "size": 40,
        "children": children_keyword_first,
    })
    # Формируем нужный формат для первых вершин (stackoverflow - как доп вершина)
    children_arxive = [
        {
            "name": "arxiv",
            "size": 40,
            "children": children
        },
        {
            "name": "stackoverflow",
            "size": 40,
        },
    ]
    # Формируем нужный формат первой вершины(фраза поиска)
    result = {
        "name": request,
        "size": 50,
        "children": children_arxive,
    }
    with open("arxiv.json", "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False)

def top_keywords(list_parsed_articles, request):
    """
    :param list_parsed_articles: список, состоящий из распарщенной информации о статьях
    :return: список топ 5 ключевых слов в статьях
    """
    all_keywords = ""
    # Склеиваем все ключевые слова из статей
    for articles in list_parsed_articles:
        if articles["keywords"] != " " and articles["keywords"] != request:
            all_keywords += articles["keywords"]
    list_words = {}
    # Разбиваем эти статьи и определяем их количество
    for word in re.findall(r'((?:\b[-а-яa-zё\d ]{2,}\b)*?)[,;.·]', all_keywords, re.I):
        list_words[word] = list_words.get(word, 0) + 1
    top_words = list(list_words.items())
    # Сортируем их по убыванию количества
    top_words.sort(key=lambda x: x[1], reverse=True)
    list_top_word = []
    # Выбираем топ-5 первых слов
    for word in top_words[:5]:
        list_top_word.append(word[0])
    print(list_top_word)
    return list_top_word


def info_on_request_arxiv(request, count_articles):
    """
    :param request: слово запроса
    :param count_articles: количество статей, которые будут просмотрены
    :return: сформированный json, нужного формата
    """
    # Первый запрос по нужному слову
    nodes = []
    nodes.append({request: scrapping_arxiv_on_request(request, count_articles)})
    # Парсинг статей и вытаскивание нужной информации
    list_parsed_articles = pdf_parser(request)
    keywords_dict1 = {}
    i = 1
    # Формирование дополнительной информации по ключевым словам
    for word1 in top_keywords(list_parsed_articles, request):
        # Формирование глубины 1
        keywords_dict1[word1] = scrapping_arxiv_on_request(word1, count_articles)
        keywords_dict2 = {}
        for word2 in top_keywords(pdf_parser(word1), request):
            # Формирование глубины 2, в кажом слове из первой ищем еще
            keywords_dict2[word2] = scrapping_arxiv_on_request(word2, count_articles)
            keywords_dict3 = {}
            for word3 in top_keywords(pdf_parser(word2), request):
                # Формирование глубины 3, в кажом слове из второй ищем еще
                keywords_dict3[word3] = scrapping_arxiv_on_request(word3, count_articles)
                print(i)
                i += 1
            keywords_dict2[word2].append({"keywords": keywords_dict3})
        keywords_dict1[word1].append({"keywords": keywords_dict2})
    nodes.append({"keywords": keywords_dict1})
    # Формирование нужного вида json
    #create_json(nodes, request)
    return nodes


pprint(info_on_request_arxiv('graph', 1))