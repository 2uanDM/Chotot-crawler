import base64
import os
import shutil
import streamlit as st
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.fetcher import fetch
from core.parser import parse_page, download
from datetime import datetime


def run_next(keyword: str, html_path: str, save_dir: str, threads: int):
    if not os.path.exists(html_path):
        st.error('Vui lòng fetch html trước khi parse và download')
        return

    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    else:
        shutil.rmtree(save_dir, ignore_errors=True)
        os.makedirs(save_dir, exist_ok=True)

    if not os.path.exists(f'{save_dir}/{keyword}'):
        os.makedirs(f'{save_dir}/{keyword}', exist_ok=True)
    else:
        shutil.rmtree(f'{save_dir}/{keyword}', ignore_errors=True)
        os.makedirs(f'{save_dir}/{keyword}', exist_ok=True)

    # Get all htmls
    htmls = [os.path.join(html_path, html) for html in os.listdir(html_path)]

    if htmls == []:
        st.error('Vui lòng fetch html trước khi parse và download')
        return

    # Parse
    all_urls = []

    with st.status('Running'):
        for html in htmls:
            result = parse_page(html)

            if result['status'] == 'error':
                st.error(f'Lỗi khi parse html: {result["msg"]}')
                continue

            urls = result['data']
            all_urls.extend(urls)

            st.write(f'Đã parse xong {html}')

        print(f"==>> all_urls: {len(all_urls)}")

        # Download
        st.write(f'Đang download tổng cộng {len(all_urls)} ảnh ...')
        with ThreadPoolExecutor(max_workers=int(threads)) as executor:
            futures = [executor.submit(download, url, f'{save_dir}/{keyword}') for url in all_urls]

            for future in as_completed(futures):
                result = future.result()

                if result['status'] == 'error':
                    st.error(f'Lỗi khi download: {result["msg"]}')
                else:
                    print(result['msg'])

        # Zip the images and download in the streamlit app
        st.write('Đang nén ảnh ...')
        datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        with zipfile.ZipFile(f'zip/{keyword}_{datetime_now}.zip', 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(f'{save_dir}/{keyword}'):
                for file in files:
                    zip_file.write(os.path.join(root, file), arcname=file)

    # Show the download link in the streamlit app
    st.write('Đã nén xong, vui lòng tải file zip ở link bên dưới')

    with open(f'zip/{keyword}_{datetime_now}.zip', 'rb') as f:
        st.download_button(
            label='Tải file zip',
            data=f,
            file_name=f'{keyword}_{datetime_now}.zip',
        )

    st.success('Đã download xong')


def run(keyword: str, max_pages: int, threads: int):
    max_pages = int(max_pages)
    threads = int(threads)
    print(f"==>> threads: {threads}")
    print(f"==>> max_pages: {max_pages}")

    urls = [f'https://xe.chotot.com/mua-ban-xe-may?q={keyword}&page={page}' for page in range(1, max_pages + 1)]

    # Fetch the htmls

    shutil.rmtree('data/urls', ignore_errors=True)
    os.makedirs('data/urls', exist_ok=True)

    with st.status('Running ...'):
        st.write('Đang fetch html ...')

        with ThreadPoolExecutor(max_workers=int(threads)) as executor:
            futures = []

            for url in urls:
                page = url.split('=')[-1]
                futures.append(executor.submit(fetch, url, f'data/urls/{keyword}_page_{page}.html'))

            for future in as_completed(futures):
                result = future.result()
                print(result)

                if result['status'] == 'error':
                    st.error(f'Lỗi khi fetch url: {result["msg"]}')
                else:
                    st.write(result['msg'])

    st.success('Đã fetch xong html')


def main():
    st.title("Chợ Tốt Image Downloader")
    st.caption("By: @2uanDM")
    st.write('Nhập keyword cần tải các ảnh từ Chợ Tốt, sau đó nhấn nút Process để bắt đầu quá trình tải ảnh.')
    st.write('Sau khi tải xong, các ảnh sẽ được nén thành file zip và có thể tải về ở phía dưới')

    st.sidebar.title("Cài đặt")
    max_pages = st.sidebar.text_input('Số page tối đa:', value=100, key='max_pages')
    threads = st.sidebar.text_input('Số luồng tối đa:', value=5, key='threads')
    st.sidebar.caption('Ví dụ, với keyword <b>honda</b> thì có tới hơn 90 trang, nên mặc định thì ta sẽ đi qua hết 100 url tương ứng page 1 đến page 100. </br> Đối với keyword nào mà bạn cảm thấy nó sẽ ít trang hơn thì bạn giảm xuống để tăng tốc độ fetch html', unsafe_allow_html=True)

    keyword = st.text_input('Nhập keyword:', key='keyword')
    fetch_html = st.button('Fetch HTMLs')
    st.write('---')
    parse_and_download = st.button('Parse & Download')

    if fetch_html:
        if keyword:
            run(keyword, max_pages, threads)
        else:
            st.info('Vui lòng nhập keyword')

    if parse_and_download:
        run_next(
            keyword=keyword,
            html_path='data/urls',
            save_dir='data/images',
            threads=threads
        )


if __name__ == "__main__":
    main()
