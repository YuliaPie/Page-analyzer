from urllib.parse import urlparse

import requests
import validators
from bs4 import BeautifulSoup


def validate_url(input_url):
    if not input_url:
        return 'URL обязателен для заполнения'
    if not validators.url(input_url):
        return 'Некорректный URL'
    if len(input_url) > 255:
        return 'Введенный URL превышает длину в 255 символов'


# эти данные нормализуем
def normalise_url(input_url):
    # делим на протокол и хост
    parsed_url = urlparse(input_url)
    # соединяем обратно через ф-строку
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def parse_url(url_name):
    url_response = requests.get(url_name)
    url_response.raise_for_status()
    soup = BeautifulSoup(url_response.text, 'html.parser')
    status_code = url_response.status_code
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.find('title').string if soup.find('title') else ''
    all_meta_tags = soup.find_all("meta")
    description = ""
    for meta_tag in all_meta_tags:
        if meta_tag.get("name") == "description":
            description = meta_tag.get('content')
            break
    return status_code, h1, title, description
