from pdf_parser import pdf_parser
from hubrhubr import info_on_request_hubr
from arxiv import info_on_request_arxiv
import json
from pprint import pprint

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



def create_json(search_result, request, resource):
    """
    :param search_result: итоговый список информации о всех нужных статьях
    :param request: фраза поиска
    :return: json файл нужного формата
    """
    pprint(search_result)
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
    children_resource = [
        {
            "name": resource,
            "size": 40,
            "children": children
        },
    ]
    return children_resource


def compare_resources(finally_children, request):
    # Формируем нужный формат первой вершины(фраза поиска)
    result = {
        "name": request,
        "size": 50,
        "children": finally_children,
    }
    with open(request + ".json", "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False)


request = "captcha"
count = 7
hubr = create_json(info_on_request_hubr(request, count), request, "hubr")
pprint(hubr)
arxiv = create_json(info_on_request_arxiv(request, count), request, "arxiv")
pprint(arxiv)
compare_resources(hubr + arxiv, request)