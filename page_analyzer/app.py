from flask import Flask, render_template, request, flash, url_for, redirect
from dotenv import load_dotenv
import os
import psycopg2
from validators import url
import datetime

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# получение объекта курсора


# Обработчик главной страницы
@app.route('/')
def show_main_page():
    return render_template(
        'index.html'
    )
# Обработчик списка сайтов (отображение)
@app.get('/urls')
def urls_get():
    with conn.cursor as curs:
        curs.execute('SELECT * FROM urls')
        all_urls = curs.fetchall()
    return render_template(
        'urls.html', all_urls=all_urls
    )
# Обработчик добавления сайта в бд
@app.post('/urls')
def post_url():
    # Извлекаем данные формы
    data = request.form['url']
    # Проверяем корректность данных
    if not url(data):
        # Если возникли ошибки, то устанавливаем код ответа в 422
        # и рендерим главную страницу
        # со флеш-сообщением об ошибке
        flash('Некорректный URL', "error")
        return redirect(url_for('show_main_page')), 422

    # Если данные корректны, то добавляем данные в базу
    # получаем текущую дату
    current_date = datetime.date.today().isoformat()
    with conn.cursor() as curs:
        curs.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s), "
                     "(data, current_date)")
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url'))
#вывод конкретного введенного URL на отдельной странице
@app.route('/urls/<int:id>')
def get_url(id):
    with conn.cursor as curs:
        curs.execute('SELECT * FROM urls WHERE id=%s", (id,)')
        url = curs.fetchall()
    if url is None:
        return 'Page not found', 404

    return render_template('show_url.html', url=url)