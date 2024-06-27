import psycopg2
from flask import (Flask, render_template, request,
                   flash, url_for, redirect, get_flashed_messages)
from dotenv import load_dotenv
import os
from requests import RequestException
from page_analyzer.db_manager import (get_urls,
                                      get_id_by_name,
                                      insert_url_get_id,
                                      get_url_by_id,
                                      get_checks_by_url_id,
                                      insert_check)
from page_analyzer.tools import normalise_url, validate_url, parse_url

load_dotenv()
app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
SECRET_KEY = app.config['SECRET_KEY']
conn = psycopg2.connect(DATABASE_URL)


@app.route('/')
def show_main_page():
    return render_template('index.html')


@app.get('/urls')
def urls_get():
    all_urls = get_urls(conn)
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
    url = get_id_by_name(conn, norm_url)
    if url:
        url_id = url[0]
        flash('Страница уже существует', 'info')
        return redirect(url_for('show_url', id=url_id))
    id = insert_url_get_id(conn, norm_url)
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', id=id))


@app.route('/urls/<int:id>')
def show_url(id):
    try:
        url = get_url_by_id(conn, id)
        if url is None:
            return render_template('error_404.html'), 404
        url_checks = get_checks_by_url_id(conn, id)
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'show_url.html',
            url=url, url_checks=url_checks, messages=messages)
    except Exception:
        return render_template('error_500.html'), 500


@app.post('/urls/<id>/checks')
def make_check(id):
    url = get_url_by_id(conn, id)
    try:
        status_code, h1, title, description = parse_url(url.name)
        insert_check(conn, id, status_code, h1, title,
                     description)
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('show_url', id=id))
    except RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('show_url', id=id))
