from bs4 import BeautifulSoup
from selenium import webdriver
import pdfkit
import re
import json


# Функция собирает информаицю о поисковом запросе, входные данные -  поисковая фраза, количество рассматриваемых статей
# На выходе массив нужной структуры
def scrapping_stackoverflow(search_phrase, count_of_articles=10):
    # Настройки для pdfkit
    path_wkthmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    # Активация селениума
    browser = webdriver.Chrome(executable_path=r"D:\Ucheba\fourthsem\Sorokin\pythonProjects\arxiv\chromedriver.exe")
    browser.get("https://ru.stackoverflow.com/search")
    browser.find_element_by_class_name("s-input").send_keys(search_phrase)
    browser.find_elements_by_class_name("s-btn__primary")[3].click()
    node_article = []
    # Ищем ссылки результатов и проходим по ним
    search_result = browser.find_elements_by_class_name("question-hyperlink")
    for number_of_result in range(0, count_of_articles):
        try:
            # Обход блокировки сайта с открытием невидимой ссылки - перемещаемся на следующую
            action = webdriver.ActionChains(browser)
            action.move_to_element(search_result[number_of_result + 1])
            action.perform()
            # Переходим на очередную статью
            search_result[number_of_result].click()
            html_search_result = BeautifulSoup(browser.page_source, "html.parser")
            name = html_search_result.find('div', {"id": "question-header"}).contents[1].text
            # Собираем ифнормацию об авторе, имя, ссылка на профиль и рейтинг
            authors = []
            author_name = html_search_result.find('div', {"class": "post-signature owner grid--cell"}).contents[1].contents[5].contents[1].text
            author_rate = html_search_result.find('div', {"class": "post-signature owner grid--cell"}).contents[1].contents[5].contents[3].contents[1].text
            author_link = "https://ru.stackoverflow.com" + html_search_result.find('div', {"class": "post-signature owner grid--cell"}).contents[1].contents[5].contents[1].attrs['href']
            authors.append({"author_name": author_name, "author_link": author_link, "author_rate": author_rate})
            # Собираем дату
            data = html_search_result.find('div', {"class": "post-signature owner grid--cell"}).contents[1].contents[1].text
            # Собираем теги
            subjects = []
            for key in range(1, len(html_search_result.find('div', {"class": "d-block"}).contents), 2):
                subjects.append(html_search_result.find('div', {"class": "d-block"}).contents[key].text)
            # Создаем пдф и записываем в нее текст вопроса
            text = "<head><meta content='text/html;charset=UTF-8' http-equiv='content-type'/></head>" + html_search_result.find('div', {"class": "post-text"}).text
            url_pdf = "articles/"+re.sub(r"[.%#&{}\\\/<>*?$!`:@+|=\"\']", "", name[:40])+".pdf"
            pdfkit.from_string(text, url_pdf, configuration=config)
            comment_with_href = []
            comment_with_code = []
            # Формируем список комментариев - если есть ссылка  - значит вносим в список,
            # есть - код вносим в другой список
            for comment in html_search_result.find_all('span', {"class": "comment-copy"}):
                for tag in comment.contents:
                    try:
                        # Проверяем содержится ли ссылка в атрибутах
                        if "href" in tag.attrs:
                            comment_text = ""
                            # Если содержится, то формируем текст комментария
                            for content in comment.contents:
                                try:
                                    #comment_text += " "+content.text
                                    # Еслми есть ссылка - вставляем ее, подписывая, что это ссылка
                                    if "href" in content.attrs:
                                        comment_text += " Ссылка: [ " + content.attrs["href"] + " ]"
                                # Если нет, то просто добавляем текст
                                except AttributeError:
                                    comment_text += str(" "+content)
                            comment_with_href.append(comment_text)
                            break
                    except AttributeError:
                        continue
                    try:
                        # Проверяем содержится ли код в комментарии
                        if "code" in tag.name:
                            comment_text = ""
                            # Если содержится, то формируем текст комментария
                            for content in comment.contents:
                                try:
                                    #comment_text += " " + content.contents[0]
                                    # Еслми есть код - вставляем ее, подписывая, что это код
                                    if "code" in content.name:
                                        comment_text += " Код: [ " + content.contents[0] + " ]"
                                # Если нет, то просто добавляем текст
                                except TypeError:
                                    comment_text += str(" " + content)
                            comment_with_code.append(comment_text)
                            break
                    except AttributeError:
                        continue
            # Формируем список ответов
            answers = []
            for answer in html_search_result.find_all('div', {"class": "answercell post-layout--right"}):
                answer_text = ""
                for key_content in range(1, len(answer.contents[1].contents), 2):
                    try:
                        # Проверяем содержится ли код в ответе
                        if "code" in answer.contents[1].contents[key_content].contents[0].name:
                            code = re.sub(r"\n", " ", answer.contents[1].contents[key_content].contents[0].text)
                            answer_text += " Код: [ " + code + " ] "
                        else:
                            # Если не содержится проверяем есть ли ссылки, либо просто добляем текст
                            answer_text += answer.contents[1].contents[key_content].contents[0].text
                            if "href" in answer.contents[1].contents[key_content].contents[0].attrs:
                                answer_text += " Ссылка: [ " + answer.contents[1].contents[key_content].contents[0].attrs["href"] + " ] "
                    except (TypeError, IndexError) as e:
                        # Проверяем есть ли ссылки
                        for tag in answer.contents[1].contents[key_content]:
                            try:
                                if "href" in tag.attrs:
                                    answer_text += " Ссылка: [ " + tag.attrs["href"] + " ] "
                            except AttributeError:
                                answer_text += tag
                answers.append(answer_text)
            # Сбор ссылок из пункта "связанные"
            links = []
            try:
                related_links = html_search_result.find_all('div', {"class": "module sidebar-linked"})[0].contents[3].contents
                for key_links in range(1, len(related_links), 2):
                    links.append({"link_article": related_links[key_links].contents[3].attrs["href"],
                                  "name_article": related_links[key_links].contents[3].text})
            except IndexError:
                pass
            # Сбор ссылок из пункта "похожие"
            similar_links = html_search_result.find_all('div', {"class": "module sidebar-related"})[0].contents[3].contents
            for key_links in range(1, len(similar_links)-1):
                links.append({"link_article": similar_links[key_links].contents[1].attrs["href"],
                              "name_article": similar_links[key_links].contents[1].text})

            node_article.append({"name": name, "authors": authors, "date": data, "subjects": subjects, "pdf_url": url_pdf,
                                 "comment_with_href": comment_with_href, "comment_with_href": comment_with_href,
                                 "answers": answers, "links": links})
            browser.back()
            # Необходимо заново выстроить DOM страницы
            search_result = browser.find_elements_by_class_name("question-hyperlink")
        except IndexError:
            print("Exception, a lot of count_of_search, search result dont have so value")
            exit()
    browser.close()
    return node_article

nodes = scrapping_stackoverflow("python pdf", 10)
with open("stackoverflow.json", "w", encoding="utf-8") as file:
    json.dump(nodes, file, ensure_ascii=False)