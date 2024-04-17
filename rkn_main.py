from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import json

# Запуск webdriver
driver = webdriver.Chrome()

i = 0
url = f'https://rkn.gov.ru/communication/register/license/p{i}/'
driver.get(url)
all_data = []

# Select(driver.find_element(By.ID, 'periodmon')).select_by_value('12')
# Select(driver.find_element(By.ID, 'periodyear')).select_by_value('2026')
Select(driver.find_element(By.ID, 'service_id')).select_by_value('1')
Select(driver.find_element(By.ID, 'lic_status_id')).select_by_value('1')
Select(driver.find_element(By.ID, 'region_id')).select_by_value('57')


driver.find_element(By.CLASS_NAME, 'buttonSearch').click()

while True:
    Select(driver.find_element(By.ID, 'service_id')).select_by_value('1')
    Select(driver.find_element(By.ID, 'lic_status_id')).select_by_value('1')
    Select(driver.find_element(By.ID, 'region_id')).select_by_value('57')

    try:
        # Открытие страницы реестра лицензий
        url = f'https://rkn.gov.ru/communication/register/license/p{i}/'
        driver.get(url)

        # Пауза для загрузки страницы
        time.sleep(1)

        # Нахождение таблицы с id ResList1
        table = driver.find_element(By.ID, "ResList1")

        # Перебор всех строк в таблице
        for row in table.find_elements(By.TAG_NAME, "tr"):
            # Получение данных из каждой ячейки
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 0:
                # Проверка, что данные в столбце "Срок действия" от 2023 года
                validity_date = cells[2].text
                if '2023' in validity_date:
                    # Сохранение данных
                    data = [cell.text for cell in cells]
                    with open('result.txt', 'w+') as file:
                        json.dump(data, file)
                    all_data.append(data)
        print(all_data)
        i += 100
    except Exception as e:
        print(e)

    # Закрытие webdriver
driver.quit()
