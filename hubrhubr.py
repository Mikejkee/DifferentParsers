import requests
from serialize import*
from bs4 import BeautifulSoup
import math

url = 'https://habr.com/'


# Получим html страницу
def get_html(url):
    r = requests.get(url)

    return r.text


# получить все ссылки на посты по поисковому запросу
def get_links_article_for_search(search_str, count_page):
    link = 'https://habr.com/search/?q=' + search_str
    next_page = link
    links = []
    count = 0

    while count < count_page:

        soup = BeautifulSoup(get_html(next_page), features='html.parser')
        link_posts = soup.findAll('a', class_='post__title_link')

        for link in link_posts:
            links.append(link.get('href'))

        try:
            next_page = 'https://habr.com' + soup.find('a', id='next_page').get('href')
            count = count + 1
        except:
            break

    return links


# формируем json данные по статье
# def create_json(name_article=None, date=None, author=None, link_author=None, rang_author=None, carma_author=None,
#                 link=None,
#                 links=None, subjects=None):
#     info_article = {
#         "name": name_article,
#         "date": date,
#         "authors":
#             {
#                 "name_autor": author,
#                 "link_author": link_author,
#                 "range_author": rang_author,
#                 "power_author": carma_author
#             },
#         "content": link,
#         "links": links,
#         "subjects": subjects
#     }
#
#     return info_article

def create_json(name_article=None, date=None, author=None, link_author=None, rang_author=None, carma_author=None,
                link=None,
                links=None, subjects=None, keywords=None):
    info_article = [name_article, "", {author, }, date, subjects, links, keywords]
    return info_article

# получаем данные со статьи
def get_info_article(link):
    soup = BeautifulSoup(get_html(link), features='html.parser')
    name_article = soup.find('h1', class_='post__title post__title_full').find('span').text
    link_author = soup.find('a', class_='post__user-info user-info').get('href')
    author = soup.find('span', class_='user-info__nickname user-info__nickname_small').text
    try:
        rang_author = soup.find('div', class_='stacked-counter__value stacked-counter__value_magenta').text
    except AttributeError:
        rang_author = ""
    try:
        carma = soup.find('div', class_='stacked-counter__value stacked-counter__value_green ')
    except AttributeError:
        carma = ""

    if carma is not None:
        carma_author = carma.text
    else:
        carma_author = '--'
    try:
        same_publication = soup.find('div', class_='default-block default-block_content'). \
            findAll('li', class_='content-list__item content-list__item_devided post-info')
    except AttributeError:
        same_publication = ""

    links = []

    for publication in same_publication:
        links.append({"link_article": publication.find('a').get('href'),
                      "name_article": publication.find('a').text})

    date = soup.find('span', class_='post__time').text
    try:
        li_subjects = soup.findAll('li', class_='inline-list__item inline-list__item_hub')
    except AttributeError:
        li_subjects = ""
    try:
        li_keywords = soup.findAll('li', class_='inline-list__item inline-list__item_tag')
    except AttributeError:
        li_keywords = ""
    subjects = []
    keywords = []

    for subject in li_subjects:
        subjects.append(subject.find('a').text)

    for keyword in li_keywords:
        keywords.append(keyword.find('a').text)

    return create_json(name_article, date, author, link_author, rang_author, carma_author, link, links, subjects, keywords)

def top_keywords(list_info_articles, request):
    """
    :param list_parsed_articles: список, состоящий из распарщенной информации о статьях
    :return: список топ 5 ключевых слов в статьях
    """
    all_keywords = []
    # Создание единого списка ключевых слов
    for info_article in list_info_articles:
        for keyword in info_article[6]:
            if keyword != request:
                all_keywords.append(keyword)
    list_words = {}
    # Разбиваем эти статьи и определяем их количество
    for word in all_keywords:
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

# получаем статьи по поисковому запросу
def get_article_for_search(search_str, count_artciles):
    count_page = math.ceil(count_artciles / 20)
    links = get_links_article_for_search(search_str, count_page)

    list_info_articles = []
    info_article = []
    all_keyword = ""
    number_of_result = 0
    for link in links:
        if number_of_result != count_artciles:
            info_article.append(get_info_article(link))
            # for keyword in get_info_article(link)[-1]:
            #     all_keyword += keyword + ", "
            #write_json(info_article, 'hubr.json')
            number_of_result += 1
        else:
            break

    #list_info_articles.append({search_str: info_article})
    #list_info_articles.append({"keywords": {}})
    #write_json(list_info_articles, 'hubr.json')
    return info_article

def info_on_request_hubr(request, count_articles):
    # Первый запрос по нужному слову
    nodes = []
    articles_first_request = get_article_for_search(request, count_articles)
    nodes.append({request: articles_first_request})
    keywords_dict1 = {}
    i = 1
    # Формирование дополнительной информации по ключевым словам
    for word1 in top_keywords(articles_first_request, request):
        # Формирование глубины 1
        articles_second_request = get_article_for_search(word1, count_articles)
        keywords_dict1[word1] = articles_second_request
        keywords_dict2 = {}
        for word2 in top_keywords(articles_second_request, word1):
            # Формирование глубины 2, в кажом слове из первой ищем еще
            articles_third_request = get_article_for_search(word2, count_articles)
            keywords_dict2[word2] = articles_third_request
            keywords_dict3 = {}
            for word3 in top_keywords(articles_third_request, word2):
                # Формирование глубины 3, в кажом слове из второй ищем еще
                articles_fourth_request = get_article_for_search(word3, count_articles)
                keywords_dict3[word3] = articles_fourth_request
                print(i)
                i += 1
            keywords_dict2[word2].append({"keywords": keywords_dict3})
        keywords_dict1[word1].append({"keywords": keywords_dict2})
    nodes.append({"keywords": keywords_dict1})
    # Формирование нужного вида json
    # create_json(nodes, request)
    return nodes
