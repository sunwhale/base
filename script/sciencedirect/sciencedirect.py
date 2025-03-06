import os
import re
import time
import json
import random

import pyhttpx
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver


def dump_json(file_path, data, encoding='utf-8'):
    """
    Write JSON data to file.
    """
    with open(file_path, 'w', encoding=encoding) as f:
        return json.dump(data, f, ensure_ascii=False)


def load_json(file_path, encoding='utf-8'):
    """
    Read JSON data from file.
    """
    with open(file_path, 'r', encoding=encoding) as f:
        return json.load(f)


def get_local_pii_values(path):
    fns = []
    for root, dirs, files in os.walk(path):
        for fn in files:
            fns.append(fn.split('.')[0])
    return fns


def download_bibtex_from_sciencedirect(pii_value: str, bib_path: str = 'bibs') -> None:
    """
    requests库遇到403错误参考：https://blog.csdn.net/SweetHeartHuaZai/article/details/130983179
    url = 'https://doi.org/10.1016/j.jmps.2022.104931'
    url = 'https://linkinghub.elsevier.com/retrieve/pii/S0022509622001284'
    url = 'https://www.sciencedirect.com/science/article/pii/S0022509622001284'
    url = 'https://www.sciencedirect.com/sdfe/arp/cite?pii=S0022509622001284&format=text%2Fx-bibtex&withabstract=true'
    url = 'https://www.sciencedirect.com/sdfe/arp/citingArticles?pii=S0022509622001284&doi=10.1016%2Fj.jmps.2022.104931'
    url = 'https://www.sciencedirect.com/sdfe/arp/pii/S0022509622001284/references?entitledToken=8AC6DBBF7834A727914337C404552FB7C7F31794ACDB3846F7EF09FC50632F2C0D3399C91B1BD982'
    """
    url = f'https://www.sciencedirect.com/sdfe/arp/cite?pii={pii_value}&format=text%2Fx-bibtex&withabstract=true'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    }
    session = pyhttpx.HttpSession()
    response = session.get(url=url, headers=headers, timeout=10, verify=False)

    if response.status_code == 200:  # 检查是否成功获取数据
        with open(os.path.join(bib_path, f'{pii_value}.txt'), 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f'{pii_value}.txt is downloaded.')
    else:
        print('Failed to retrieve data. Status code:', response.status_code)


def download_html_code_from_sciencedirect(driver, pii_value: str, sleep_time: float = 5.0, html_path: str = 'htmls') -> None:
    driver.get(f'https://www.sciencedirect.com/science/article/pii/{pii_value}')
    time.sleep(sleep_time)
    html_code = driver.page_source
    if str(pii_value) in html_code:
        print(f'download_html_code_from_sciencedirect with pii {pii_value} is Done')
        with open(os.path.join(html_path, f'{pii_value}.html'), 'w', encoding='utf-8') as f:
            f.write(html_code)
    else:
        raise NotImplementedError('Stopped')


def analyze_html_code(pii_value: str, html_path: str = 'htmls', json_path: str = 'jsons') -> None:
    with open(os.path.join(html_path, f'{pii_value}.html'), 'r', encoding='utf-8') as f:
        html_code = f.read()

    soup = BeautifulSoup(html_code, 'html.parser')

    cited_pii_list = find_cited_pii(soup)
    ref_pii_list = find_ref_pii(soup)
    cited_count = find_cited_count(soup)

    data = {
        'cited_count': cited_count,
        'cited_pii': cited_pii_list,
        'ref_pii': ref_pii_list,
    }

    dump_json(os.path.join(json_path, f'{pii_value}.json'), data, encoding='utf-8')


def analyze_related_html_code(pii_value: str, html_path: str = 'htmls', json_path: str = 'jsons') -> None:
    data = load_json(os.path.join(json_path, f'{pii_value}.json'), encoding='utf-8')
    related_pii_values = data['cited_pii'] + data['ref_pii']
    local_pii_values = get_local_pii_values(json_path)
    for related_pii_value in related_pii_values:
        if related_pii_value not in local_pii_values:
            analyze_html_code(related_pii_value, html_path, json_path)


def download_related_bibtex(pii_value: str, json_path: str = 'jsons', bib_path: str = 'bibs') -> None:
    data = load_json(os.path.join(json_path, f'{pii_value}.json'), encoding='utf-8')
    related_pii_values = data['cited_pii'] + data['ref_pii']
    local_pii_values = get_local_pii_values(bib_path)
    for related_pii_value in related_pii_values:
        if related_pii_value not in local_pii_values:
            download_bibtex_from_sciencedirect(related_pii_value, bib_path)
            time.sleep(random.random())


def find_pdf_url(soup: BeautifulSoup) -> str:
    a_block = soup.find('a', {'class': 'link-button accessbar-utility-component accessbar-utility-link link-button-primary link-button-icon-left'})
    if a_block:
        return a_block.get('href')
    else:
        return ''


def find_ref_pii(soup: BeautifulSoup) -> list[str]:
    pii_list = []
    ol_block = soup.find('ol', {'class': 'references'})
    if ol_block:
        for li in ol_block.find_all('li'):
            a_block = li.find('a', {'class': 'anchor link anchor-primary'})
            if a_block:
                if a_block.text == 'View article':
                    pii_list.append(a_block.get('href').split('/')[-1])
            else:
                print("未找到<a>代码块")
    else:
        print("未找到<ol>代码块")
    return pii_list


def find_cited_pii(soup: BeautifulSoup) -> list[str]:
    pii_list = []
    div_block = soup.find('div', {'id': 'section-cited-by'})
    if div_block:
        for a in div_block.find_all('a', {'class': 'anchor anchor-primary'}):
            if '/science/article/pii' in a.get('href'):
                pii_list.append(a.get('href').split('/')[-1])
    else:
        print("未找到<div>代码块")
    return pii_list


def find_cited_count(soup: BeautifulSoup) -> int:
    div_block = soup.find('div', {'id': 'section-cited-by'})
    if div_block:
        h2_block = div_block.find('h2', {'class': 'u-h4 u-margin-l-ver u-font-serif'})
        if h2_block:
            result = re.search(r'\d+', h2_block.text)
            if result:
                number = result.group()
                return int(number)
            else:
                return -1
        else:
            print("未找到<h2>代码块")
    else:
        print("未找到<div>代码块")
    return -1


def download_related_html(driver, pii_value: str, json_path: str = 'jsons', html_path: str = 'htmls') -> None:
    data = load_json(os.path.join(json_path, f'{pii_value}.json'), encoding='utf-8')
    related_pii_values = data['cited_pii'] + data['ref_pii']
    local_pii_values = get_local_pii_values(html_path)
    for related_pii_value in related_pii_values:
        if related_pii_value not in local_pii_values:
            download_html_code_from_sciencedirect(driver, related_pii_value)
            time.sleep(random.random())


def get_top_cited(pii_value: str, top_number: int = 3, json_path: str = 'jsons') -> tuple:
    data = load_json(os.path.join(json_path, f'{pii_value}.json'), encoding='utf-8')
    cited_list = []
    for cited_pii_value in data['cited_pii']:
        cited_count = load_json(os.path.join(json_path, f'{cited_pii_value}.json'), encoding='utf-8')['cited_count']
        cited_list.append([cited_pii_value, cited_count])
    ref_list = []
    for ref_pii_value in data['ref_pii']:
        cited_count = load_json(os.path.join(json_path, f'{ref_pii_value}.json'), encoding='utf-8')['cited_count']
        ref_list.append([ref_pii_value, cited_count])

    # 按第二列排序二维列表
    sorted_cited_list = sorted(cited_list, key=lambda x: x[1])
    sorted_ref_list = sorted(ref_list, key=lambda x: x[1])
    return [s[0] for s in sorted_cited_list[-top_number:]], [s[0] for s in sorted_ref_list[-top_number:]]


def recursive_download(driver, pii_value: str, depth: int = 0, max_depth: int = 2, json_path: str = 'jsons', bib_path: str = 'bibs',
                       html_path: str = 'htmls') -> None:
    depth += 1
    if depth <= max_depth:
        download_html_code_from_sciencedirect(driver, pii_value, 5.0 + 5.0 * random.random(), html_path)
        analyze_html_code(pii_value, html_path, json_path)
        download_related_bibtex(pii_value, json_path, bib_path)
        download_related_html(driver, pii_value, json_path, html_path)
        analyze_related_html_code(pii_value, html_path, json_path)
        top_cited_list, top_ref_list = get_top_cited(pii_value, 5, json_path)
        for next_pii_value in set(top_cited_list + top_ref_list):
            recursive_download(driver, next_pii_value, depth, max_depth, json_path, bib_path, html_path)
    else:
        pass


if __name__ == '__main__':
    pii_value = 'S0022509622001284'
    driver = webdriver.Edge()
    recursive_download(driver, pii_value, 0, 1)

    # driver.quit()
