import io
import json


# Запишем словарь в файл JSON
def write_json(data, path):
    with io.open(path, 'a', encoding='utf8') as outfile:
        str_ = json.dumps(data,
                          indent=4, sort_keys=True,
                          separators=(',', ': '), ensure_ascii=False)
        outfile.write(str_)