from flask import Flask, render_template, request, flash, url_for, redirect
from dotenv import load_dotenv
import os
import psycopg2
import datetime
import validators


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
    with conn.cursor() as curs:
        # передаем  SQL-запрос
        # чтобы выбрать всё из таблицы urls
        curs.execute('SELECT * FROM urls')
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
def post_url():
    # Извлекаем данные формы
    data_url = request.form['url']
    # Проверяем корректность данных
    # с помощью функции url из пакета validators
    # она проверяет, является ли значение
    # допустимым URL - адресом
    if not validators.url(data_url):
        # это не допустимый адрес, то устанавливаем код ответа в 422
        # и рендерим главную страницу
        # со флеш-сообщением об ошибке
        flash('Некорректный URL', "error")
        return redirect(url_for('show_main_page')), 422

    # Если данные корректны, то добавляем данные в базу
    # получаем текущую дату
    current_date = datetime.date.today().isoformat()
    # через курсор и контекстный менеджер
    with conn.cursor() as curs:
        # добавляем в БД новый url с инфой из формы и текущей датой
        # id у нас генерируется сам
        curs.execute(f"INSERT INTO urls (name, created_at) VALUES ('{data_url}',"
                     f" '{current_date}')")
# добавляем флеш-сообщение об успеха
    flash('Страница успешно добавлена', 'success')
    # делаем редирект на страницу нового url
    # для этого нам нужно знать его id
    # с помощью курсора и контекстного менеджера
    # ищем в бд id того url имя которого совпадает с текущим
    # сохраняем результат в переменную
    # делаем редирект на страницу с id - этой переменной
    with conn.cursor() as curs:
        curs.execute('SELECT id FROM urls WHERE name=%s;', (data_url,))
        new_id = curs.fetchone()
    return redirect(url_for('urls_get', id=new_id))


# вывод конкретного введенного URL на отдельной странице
# обработчик маршрута принимает параметр url_id
# Функция get_url(url_id) принимает значение url_id из URL-адреса


@app.route('/urls/<url_id>')
def get_url(url_id):
    # связываеемся с БД  через контекстный менеджер
    with conn.cursor() as curs:
        curs.execute(f'SELECT * FROM urls WHERE id={url_id}')
        this_url = curs.fetchall()
    if this_url is None:
        return 'Page not found', 404
    return render_template('show_url.html', url=this_url)
