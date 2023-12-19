import time
import os
import sys
import traceback
sys.path.append(os.getcwd())  # NOQA

from utils.selenium import ChromeDriver

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def fetch(url: str, save_path: str):
    max_retry = 3

    while max_retry > 0:
        try:
            print(f'========> Fetching {url} ...')

            driver = ChromeDriver(headless=True).driver
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='list-view']"))
            )

            # Scroll to bottom
            for i in range(100):
                driver.execute_script("scrollBy(0,500)")
                time.sleep(0.05)

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            driver.close()
        except Exception as e:
            error = f"Error: {str(e)}"
            print(traceback.format_exc())
            max_retry -= 1
            continue
        else:
            return {
                'status': 'success',
                'msg': f'OK: {url}',
                'data': None
            }

    return {
        'status': 'error',
        'msg': url,
        'data': None
    }


if __name__ == '__main__':
    url = 'https://xe.chotot.com/mua-ban-xe-may?q=honda&page=100'
    save_path = 'data'
    fetch(url, save_path)
