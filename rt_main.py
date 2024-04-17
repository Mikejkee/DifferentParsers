from rt_scrapper import main_scrapper, to_database
import json
import time


# news_info = main_scrapper()
# print(news_info)
# to_database(news_info)
#
#
# with open('news.json', 'w+', encoding='utf-8') as f:
#     json.dump(news_info, f, ensure_ascii=False, indent=2)

with open('news.json', 'r', encoding='utf-8') as f:
    file = json.load(f)
to_database(file)