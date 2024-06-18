from flask import Flask, render_template, request, flash, url_for, redirect
from dotenv import load_dotenv
import os
import psycopg2
from datetime import date
import validators
from psycopg2.extras import NamedTupleCursor
from urllib.parse import urlparse

# загрузкa файлa .env
# в нем: "export DATABASE_URL=postgresql://postgres:ПАРОЛЬ@localhost:5432/postgres"
# SECRET_KEY=<КЛЮЧ>
# этот файл у нас добавлен в .gitignore
# также у нас должна быть создана БД через оболочку psql
# команда та же, что прописана в database.sql
load_dotenv()
# назначаем БД через обращение к переменной среды DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL')
# подключаемся к базе данных
conn = psycopg2.connect(DATABASE_URL)
# создаем объект класса Flask, передав аргументом имя модуля
app = Flask(__name__)
# извлекаем ключ из переменных окружения
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


# Обработчик главной страницы. Просто рендерим форму
@app.route('/')
def show_main_page():
    return render_template(
        'index.html'
    )


# Обработчик списка сайтов (отображение)


@app.get('/urls')
def urls_get():
    # связываеемся с БД  через контекстный менеджер
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        # передаем  SQL-запрос
        # чтобы выбрать всё из таблицы urls
        curs.execute('SELECT * FROM urls ORDER BY id DESC')
        # сохраняем результат в переменную
        # Для получения результата после выполнения запроса
        # используем команду
        # cursor.fetchall() — вернуть все строки
        all_urls = curs.fetchall()
        # рендерим шаблон списка сайтов, передав в него
        # результат запроса через переменную
    return render_template(
        'urls.html', all_urls=all_urls
    )


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
        # Если есть ошибка валидации, показываем сообщение об ошибке и возвращаем исходный URL обратно в форму
        flash(error_msg, 'danger')
        return render_template(
            'index.html',
            url=get_url,  # Возвращаем исходный URL обратно в форму
        ), 422

    # Проверяем, существует ли URL в базе данных
    with conn.cursor() as curs:
        curs.execute('SELECT id FROM urls WHERE name=%s', (norm_url,))
        id_of_existing_url = curs.fetchone()
        print(id_of_existing_url)
        if id_of_existing_url:
            id_of_existing_url = id_of_existing_url[0]
            print(id_of_existing_url)
            with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
                curs.execute(f'SELECT * FROM urls WHERE id={id_of_existing_url}')
                url = curs.fetchone()
                print(url)
            flash('Страница уже существует', 'warning')
            return redirect(url_for('urls_get', id=id_of_existing_url))

    # Если URL не существует, добавляем его в базу данных
    with conn.cursor() as curs:
        # добавляем в БД новый url с инфой из формы и текущей датой
        # id у нас генерируется сам, возвращаем его и сохраняем в переменную
        current_date = date.today().isoformat()
        curs.execute(
            "INSERT INTO urls (name, created_at)\
            VALUES (%s, %s)\
            RETURNING id;",
            (norm_url, current_date),
        )
        new_id = curs.fetchone()[0]
    # теперь выбираем из таблицы данные на новую запись
    # используем NamedTupleCursor, чтобы вернуть данные в виде именованного кортежа:
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f'SELECT * FROM urls WHERE id={new_id}')
        url = curs.fetchone()
    # добавляем флеш-сообщение об успехе
    flash('Страница успешно добавлена', 'success')
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


"""
@app.post('/urls')
def post_url():
    # Извлекаем данные формы
    data_url = request.form['url']
    # проверяем что url не больше 255 символов
    if len(data_url) > 255:
        print("long url")
        #flash('URL превышает 255 символов', "error")
        return redirect(url_for('show_main_page')), 422
    # эти данные нормализуем
    # делим на протокол и хост
    parsed_url = urlparse(data_url)
    # соединяем обратно через ф-строку
    normalised_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    # Проверяем корректность данных
    # 1) что адрес не встречался раньше в бд
    # извлечем все имена из бд
    with conn.cursor() as curs:
        curs.execute('SELECT id FROM urls WHERE name=%s', (normalised_url,))
        id_of_existing_url = curs.fetchone()
        print(id_of_existing_url)
        if id_of_existing_url:
            id_of_existing_url = id_of_existing_url[0]
            print(id_of_existing_url)
            with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
                curs.execute(f'SELECT * FROM urls WHERE id={id_of_existing_url}')
                url = curs.fetchone()
                print(url)
            flash('Страница уже существует', 'alert alert-info')
            return redirect(url_for('show_url', url_id=id_of_existing_url, url=url))


    # с помощью функции url из пакета validators
    # она проверяет, является ли значение
    # допустимым URL - адресом
    if not validators.url(normalised_url):
        # это не допустимый адрес, то устанавливаем код ответа в 422
        # и рендерим главную страницу
        # со флеш-сообщением об ошибке
        flash('Некорректный URL', "error")
        return redirect(url_for('show_main_page')), 422

    # Если данные корректны, то добавляем данные в базу
    # получаем текущую дату
    # через курсор и контекстный менеджер
    with conn.cursor() as curs:
        # добавляем в БД новый url с инфой из формы и текущей датой
        # id у нас генерируется сам, возвращаем его и сохраняем в переменную
        current_date = date.today().isoformat()
        curs.execute(
            "INSERT INTO urls (name, created_at)\
            VALUES (%s, %s)\
            RETURNING id;",
            (normalised_url, current_date),
        )
        new_id = curs.fetchone()[0]
    # теперь выбираем из таблицы данные на новую запись
    # используем NamedTupleCursor, чтобы вернуть данные в виде именованного кортежа:
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f'SELECT * FROM urls WHERE id={new_id}')
        url = curs.fetchone()
    # добавляем флеш-сообщение об успехе
    flash('Страница успешно добавлена', 'success')
    # делаем редирект на страницу нового url
    return redirect(url_for('show_url', url_id=new_id, url=url))


# вывод конкретного введенного URL на отдельной странице
# обработчик маршрута принимает параметр url_id
# Функция get_url(url_id) принимает значение url_id из URL-адреса
"""


@app.route('/urls/<url_id>')
def show_url(url_id):
    # используем NamedTupleCursor, чтобы вернуть данные в виде именованного кортежа:
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f'SELECT * FROM urls WHERE id={url_id}')
        url = curs.fetchone()
    return render_template('show_url.html', url=url)
