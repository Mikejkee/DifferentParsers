from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO
from io import open
import os
import re

re._MAXCACHE = 10000


def readPDF(pdfFlle):
    """
    :param pdfFlle: файл для чтения
    :return: строка, сформированная из пдф
    """
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    devlce = TextConverter(rsrcmgr, retstr, laparams=laparams)
    process_pdf(rsrcmgr, devlce, pdfFlle)
    devlce. close()
    content = retstr.getvalue()
    retstr. close()
    return content

def pdf_parser(request):
    """
    :param request: фраза поиска
    :return: список статей распарщеной информацией
    """
    result = []
    # Идем по всем статьям в каталоге поиска
    for directory in os.walk("articles\\" + request):
            for filename in directory[2]:
                # Открываем файл
                with open(str(directory[0]) + "\\" + filename, 'rb') as file:
                    outputString = readPDF(file)
                # Вытаскиваем анотацию
                abstract = re.search("Abstract(.*?)(?:Keywords|Key words|Key Words|Introduction)", outputString, re.S | re.I)
                try:
                    abstract = re.sub(r"\n", " ", abstract[1])
                except TypeError:
                    abstract = ""
                # Вытаскиваем Ключевые слова
                keywords = re.search("(?:Keywords|Key words and phrases|Key words|Key Words)[:.]*(.*?)(?:\.|Introduction)", outputString, re.S | re.I)
                try:
                    keywords = re.sub(r"\n", " ", keywords[1])
                    keywords = re.sub(r"\s{2,}", " ", keywords) + "."
                    keywords = re.sub(r" ([.,;·])", "\\1", keywords)
                except TypeError:
                    keywords = " "
                # Вытаскиваем ссылки
                references = re.search("References(.*)", outputString, re.S | re.I)
                try:
                    references = re.sub(r"\n", " ", references[1])
                except TypeError:
                    references = ""
                result.append(
                        {
                            "abstract": abstract,
                            "keywords": keywords,
                            "references": references,
                        }
                    )
    return result

#pdf_parser("math")