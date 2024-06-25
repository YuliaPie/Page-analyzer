from bs4 import BeautifulSoup
from flask import (Flask, render_template, request,
                   flash, url_for, redirect, get_flashed_messages)
from dotenv import load_dotenv
import os
import requests
from requests import RequestException
from page_analyzer.db_manager import (db_get_urls,
                                      db_get_id_by_name,
                                      db_add_url_get_id,
                                      db_get_url_by_id,
                                      db_get_checks_by_url_id,
                                      db_add_check)
from page_analyzer.tools import normalise_url, validate_url

load_dotenv()
app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
SECRET_KEY = app.config['SECRET_KEY']


@app.route('/')
def show_main_page():
    return render_template('index.html')


@app.get('/urls')
def urls_get():
    all_urls = db_get_urls(DATABASE_URL)
    messages = get_flashed_messages(with_categories=True)
    return render_template('urls.html', all_urls=all_urls, messages=messages, )


@app.post('/urls')
def add_url():
    get_url = request.form['url']
    norm_url = normalise_url(get_url)
    error_msg = validate_url(norm_url)
    if error_msg:
        flash(error_msg, 'danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=get_url, messages=messages), 422
    url = db_get_id_by_name(DATABASE_URL, norm_url)
    if url:
        url_id = url[0]
        flash('Страница уже существует', 'info')
        return redirect(url_for('show_url', id=url_id))
    id = db_add_url_get_id(DATABASE_URL, norm_url)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', id=id))


@app.route('/urls/<int:id>')
def show_url(id):
    try:
        url = db_get_url_by_id(DATABASE_URL, id)
        if url is None:
            return render_template('error_404.html'), 404
        url_checks = db_get_checks_by_url_id(DATABASE_URL, id)
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'show_url.html',
            url=url, url_checks=url_checks, messages=messages)
    except Exception:
        return render_template('error_500.html'), 500


@app.post('/urls/<id>/checks')
def make_check(id):
    url = db_get_url_by_id(DATABASE_URL, id)
    try:
        status_code, h1, title, description = parse_url(url.name)
        db_add_check(DATABASE_URL, id, status_code, h1, title,
                     description)
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('show_url', id=id))
    except RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('show_url', id=id))


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
