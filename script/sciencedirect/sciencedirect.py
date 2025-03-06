import os
import re
import time
import json

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


def download_html_code_from_sciencedirect(driver, pii_value: str, sleep_time: int = 5, html_path: str = 'htmls') -> None:
    driver.get(f'https://www.sciencedirect.com/science/article/pii/{pii_value}')
    time.sleep(sleep_time)
    html_code = driver.page_source
    print(f'get_rendered_source_code_from_sciencedirect: Done')
    with open(os.path.join(html_path, f'{pii_value}.html'), 'w', encoding='utf-8') as f:
        f.write(html_code)


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


if __name__ == '__main__':
    pii_value = 'S0022509622001284'
    # driver = webdriver.Edge()
    # rendered_source_code = download_html_code_from_sciencedirect(driver, pii_value)
    analyze_html_code('S0022509622001284')

    # identifier_value_list = find_references_identifier_value_in_html(rendered_source_code)
    # print(find_cited_count_in_html(rendered_source_code))
    # print(find_cited_pii_in_html(rendered_source_code))
    # print(find_references_pii_in_html(rendered_source_code))
    # for identifier_value in identifier_value_list:
    #     download_bibtex_from_sciencedirect(identifier_value)
    # driver.quit()
