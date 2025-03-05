import os
import re
import time

import pyhttpx
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver


def download_bibtex_from_sciencedirect(identifier_value: str) -> None:
    """
    requests库遇到403错误参考：https://blog.csdn.net/SweetHeartHuaZai/article/details/130983179
    url = 'https://doi.org/10.1016/j.jmps.2022.104931'
    url = 'https://linkinghub.elsevier.com/retrieve/pii/S0022509622001284'
    url = 'https://www.sciencedirect.com/science/article/pii/S0022509622001284'
    url = 'https://www.sciencedirect.com/sdfe/arp/cite?pii=S0022509622001284&format=text%2Fx-bibtex&withabstract=true'
    url = 'https://www.sciencedirect.com/sdfe/arp/citingArticles?pii=S0022509622001284&doi=10.1016%2Fj.jmps.2022.104931'
    url = 'https://www.sciencedirect.com/sdfe/arp/pii/S0022509622001284/references?entitledToken=8AC6DBBF7834A727914337C404552FB7C7F31794ACDB3846F7EF09FC50632F2C0D3399C91B1BD982'
    """
    url = f'https://www.sciencedirect.com/sdfe/arp/cite?pii={identifier_value}&format=text%2Fx-bibtex&withabstract=true'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    }
    session = pyhttpx.HttpSession()
    response = session.get(url=url, headers=headers, timeout=10, verify=False)

    if response.status_code == 200:  # 检查是否成功获取数据
        with open(f'{identifier_value}.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f'{identifier_value}.txt is downloaded.')
    else:
        print('Failed to retrieve data. Status code:', response.status_code)


def get_rendered_source_code_from_sciencedirect(driver, identifier_value: str, sleep_time: int = 5) -> str:
    driver.get(f'https://www.sciencedirect.com/science/article/pii/{identifier_value}')
    time.sleep(sleep_time)
    rendered_source_code = driver.page_source
    print(f'get_rendered_source_code_from_sciencedirect: Done')
    with open(os.path.join('files', f'{identifier_value}.html'), 'w', encoding='utf-8') as f:
        f.write(rendered_source_code)
    return rendered_source_code


def find_pdf_url_in_html(html_code: str) -> str:
    soup = BeautifulSoup(html_code, 'html.parser')
    a_block = soup.find('a', {'class': 'link-button accessbar-utility-component accessbar-utility-link link-button-primary link-button-icon-left'})
    if a_block:
        return a_block.get('href')
    else:
        return ''


def find_references_pii_in_html(html_code: str) -> list[str]:
    pii_list = []
    soup = BeautifulSoup(html_code, 'html.parser')
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


def find_cited_pii_in_html(html_code: str) -> list[str]:
    pii_list = []
    soup = BeautifulSoup(html_code, 'html.parser')
    div_block = soup.find('div', {'id': 'section-cited-by'})
    if div_block:
        for a in div_block.find_all('a', {'class': 'anchor anchor-primary'}):
            if '/science/article/pii' in a.get('href'):
                pii_list.append(a.get('href').split('/')[-1])
    else:
        print("未找到<div>代码块")
    return pii_list


def find_cited_count_in_html(html_code: str) -> int:
    soup = BeautifulSoup(html_code, 'html.parser')
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
    # driver = webdriver.Edge()
    identifier_value = 'S0022509623000972'
    # rendered_source_code = get_rendered_source_code_from_sciencedirect(driver, identifier_value)
    with open(os.path.join('files', f'{identifier_value}.html'), 'r', encoding='utf-8') as f:
        rendered_source_code = f.read()

    # identifier_value_list = find_references_identifier_value_in_html(rendered_source_code)
    print(find_cited_count_in_html(rendered_source_code))
    print(find_cited_pii_in_html(rendered_source_code))
    print(find_references_pii_in_html(rendered_source_code))
    # for identifier_value in identifier_value_list:
    #     download_bibtex_from_sciencedirect(identifier_value)
    # driver.quit()
