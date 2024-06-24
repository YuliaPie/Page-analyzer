from bs4 import BeautifulSoup
from flask import (Flask, render_template, request,
                   flash, url_for, redirect, get_flashed_messages)
from dotenv import load_dotenv
import os
import psycopg2
from datetime import date
import validators
from psycopg2.extras import NamedTupleCursor
from urllib.parse import urlparse
import requests
from requests import RequestException

# загрузкa файлa .env
# в нем: "export DATABASE_URL=postgresql://
# postgres:ПАРОЛЬ@localhost:5432/postgres"
# SECRET_KEY=<КЛЮЧ>
# этот файл у нас добавлен в .gitignore
# БД создана через оболочку psql, команда та же, что прописана в database.sql
load_dotenv()
# назначаем БД через обращение к переменной среды DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL')
# создаем объект класса Flask, передав аргументом имя модуля
app = Flask(__name__)
# извлекаем ключ из переменных окружения
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


# Обработчик главной страницы
@app.route('/')
def show_main_page():
    return render_template('index.html')


# Обработчик списка сайтов (отображение)
@app.get('/urls')
def urls_get():
    # подключаемся к базе данных
    conn = psycopg2.connect(DATABASE_URL)
    # связываеемся с БД  через контекстный менеджер с cursor_factory
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        # передаем  SQL-запрос
        # чтобы выбрать всё из таблиц urls + url_checks
        curs.execute("""WITH RankedUrlChecks AS
        (SELECT uc.url_id, uc.status_code, uc.created_at,
        ROW_NUMBER() OVER(PARTITION BY uc.url_id
        ORDER BY uc.created_at DESC) AS rn
        FROM url_checks uc)
        SELECT urls.url_id, urls.name,
        uc.status_code, uc.created_at
        FROM urls
        LEFT JOIN RankedUrlChecks uc
        ON urls.url_id = uc.url_id AND uc.rn = 1
        ORDER BY urls.url_id DESC;""")
        # сохраняем результат в переменную
        all_urls = curs.fetchall()
    conn.close()  # закрываем соединение
    # ловим флеш-сообщения
    messages = get_flashed_messages(with_categories=True)
    # рендерим шаблон списка сайтов, передав в него результат запроса
    return render_template('urls.html', all_urls=all_urls, messages=messages, )


# Обработчик добавления сайта в бд
@app.post('/urls')
def add_url():
    # Получаем URL из формы
    get_url = request.form['url']
    # Нормализуем введённый URL
    norm_url = normalise_url(get_url)
    # Проверяем корректность URL
    error_msg = validate_url(norm_url)
    if error_msg:
        # Если есть ошибка валидации, показываем сообщение
        # об ошибке и возвращаем исходный URL обратно в форму
        flash(error_msg, 'danger')
        # ловим флеш-сообщения
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            # Возвращаем исходный URL обратно в форму
            url=get_url, messages=messages), 422

    # Проверяем, существует ли URL в базе данных
    # подключаемся к базе данных
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as curs:
        curs.execute('SELECT url_id FROM urls WHERE name=%s', (norm_url,))
        url = curs.fetchone()
    conn.close()  # закрываем соединение
    if url:
        url_id = url[0]
        flash('Страница уже существует', 'info')
        return redirect(url_for('urls_get', id=url_id))

    # Если URL не существует, добавляем его в базу данных
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as curs:
        # добавляем в БД новый url с инфой из формы и текущей датой
        # id у нас генерируется сам, возвращаем его и сохраняем в переменную
        current_date = date.today().isoformat()
        curs.execute(
            "INSERT INTO urls (name, created_at)\
            VALUES (%s, %s)\
            RETURNING url_id;",
            (norm_url, current_date),
        )
        new_id = curs.fetchone()[0]
    conn.commit()
    conn.close()

    # теперь выбираем из таблицы данные на новую запись
    # используем NamedTupleCursor,
    # чтобы вернуть данные в виде именованного кортежа:
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f'SELECT * FROM urls WHERE url_id={new_id}')
        url = curs.fetchone()
    conn.close()
    # добавляем флеш-сообщение об успехе
    flash('Страница успешно добавлена', 'info')
    # делаем редирект на страницу нового url
    return redirect(url_for('show_url', url_id=new_id, url=url))


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


@app.route('/urls/<int:url_id>')
def show_url(url_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("SELECT * FROM urls WHERE url_id = %s", (url_id,))
            url = curs.fetchone()
        conn.close()
        if url is None:
            return render_template('error_404.html'), 404
        conn = psycopg2.connect(DATABASE_URL)
        # забираем новую запись о проверке с бд
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("SELECT * FROM url_checks \
            WHERE url_id=%s ORDER BY check_id DESC", (url_id,))
            url_checks = curs.fetchall()
        conn.close()
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'show_url.html',
            url=url, url_checks=url_checks, messages=messages)
    except Exception:
        return render_template('error_500.html'), 500


# создание новой проверки
@app.post('/urls/<url_id>/checks')
def make_check(url_id):
    # получаем снова всю инфу про наш урл
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f'SELECT * FROM urls WHERE url_id={url_id}')
        url = curs.fetchone()
    conn.close()
    try:
        # пробуем сделать запрос на сайт
        url_response = requests.get(url.name)
        # при ответе больше 400 вызовем ошибку
        url_response.raise_for_status()
        # добавим запись о проверке в бд
        conn = psycopg2.connect(DATABASE_URL)
        soup = BeautifulSoup(url_response.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else ''
        title = soup.find('title').string if soup.find('title') else ''
        meta_description = soup.find("meta", property="og:description")
        description = meta_description.get("content") \
            if meta_description else ""
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO url_checks (url_id,"
                "status_code, h1, "
                "title, description,"
                "created_at)\
                VALUES (%s, %s, %s, %s, %s, %s)\
                RETURNING check_id;",
                (url_id, url_response.status_code, h1, title,
                 description, date.today().isoformat()),
            )
        conn.commit()
        conn.close()
        return redirect(url_for('show_url', url_id=url_id))
    except RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('show_url', url_id=url_id))
