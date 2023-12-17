import os
import sys
import traceback
sys.path.append(os.getcwd())  # NOQA

import requests
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_page(html_path: str):
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # First, try to find: Không tìm thấy kết quả từ khóa đã nhập
        if '<b style="font-size: 20px;">Không tìm thấy kết quả từ khóa đã nhập</b>' in html:
            return {
                'status': 'error',
                'msg': 'Không tìm thấy kết quả từ khóa đã nhập',
                'data': None
            }

        urls = []
        soup = bs(html, 'html.parser')

        # list-view class
        list_view_class = soup.find('div', {'class': 'list-view'})

        # uls
        uls = list_view_class.find_all('ul')

        for ul in uls:
            divs = ul.find_all('div', {'role': 'button'})
            for div in divs:
                pic = div.find('picture', {'class': 'webpimg-container'})
                if pic:
                    img = pic.find('img')
                    if img:
                        source = img.get('src')
                        urls.append(source)

        return {
            'status': 'success',
            'msg': 'OK',
            'data': urls
        }
    except Exception as e:
        error = f"Error: {str(e)}"
        print(traceback.format_exc())
        return {
            'status': 'error',
            'msg': error,
            'data': None
        }


def download(url: str, save_dir: str):
    try:
        name = url.split('/')[-1]
        suffix = name.split('.')[-1]

        if suffix not in ['jpg', 'png', 'jpeg', 'webp']:
            return

        response = requests.get(url)

        with open(f'{save_dir}/{name}', 'wb') as f:
            f.write(response.content)
    except Exception as e:
        error = f"Error: {str(e)}"
        print(traceback.format_exc())
        return {
            'status': 'error',
            'msg': error,
            'data': None
        }
    else:
        return {
            'status': 'success',
            'msg': f'OK {name}',
            'data': None
        }


if __name__ == '__main__':
    html = 'data/test.html'
    result = parse_page(html)

    if result['status'] == 'error':
        print(result['msg'])
        exit(1)

    urls = result['data']
    save_dir = 'data/images'
    os.makedirs(save_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download, url, save_dir) for url in urls]
        for future in as_completed(futures):
            result = future.result()
            print(result)
