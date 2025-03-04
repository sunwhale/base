import os
import re
import time

import pyhttpx
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver


def find_references_identifier_value_in_html(html_code: str) -> list[str]:
    identifier_value_list = []
    soup = BeautifulSoup(html_code, 'html.parser')
    ol_block = soup.find('ol', {'class': 'references'})
    if ol_block:
        for li in ol_block.find_all('li'):
            a_block = li.find('a', {'class': 'anchor link anchor-primary'})
            if a_block:
                if a_block.text == 'View article':
                    identifier_value_list.append(a_block.get('href').split('/')[-1])
            else:
                print("未找到<span>代码块")
    else:
        print("未找到<ol>代码块")
    return identifier_value_list


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
    return rendered_source_code


if __name__ == '__main__':
    driver = webdriver.Edge()
    rendered_source_code = get_rendered_source_code_from_sciencedirect(driver, 'S0022509622001284')
    identifier_value_list = find_references_identifier_value_in_html(rendered_source_code)
    for identifier_value in identifier_value_list:
        download_bibtex_from_sciencedirect(identifier_value)
    driver.quit()
