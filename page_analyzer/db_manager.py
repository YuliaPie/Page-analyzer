from datetime import date
import psycopg2
from psycopg2.extras import NamedTupleCursor


def db_get_urls(DATABASE_URL):
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
    return all_urls


def db_get_id_by_name(DATABASE_URL, name):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as curs:
        curs.execute('SELECT url_id FROM urls WHERE name=%s', (name,))
        url_id = curs.fetchone()
    conn.close()
    return url_id


def db_add_url_get_id(DATABASE_URL, name):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as curs:
        # добавляем в БД новый url с инфой из формы и текущей датой
        # id у нас генерируется сам, возвращаем его и сохраняем в переменную
        current_date = date.today().isoformat()
        curs.execute(
            "INSERT INTO urls (name, created_at)\
            VALUES (%s, %s)\
            RETURNING url_id;",
            (name, current_date),
        )
        id = curs.fetchone()[0]
    conn.commit()
    conn.close()
    return id


def db_get_url_by_id(DATABASE_URL, id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("SELECT * FROM urls WHERE url_id = %s", (id,))
        url = curs.fetchone()
    conn.close()
    return url


def db_get_checks_by_url_id(DATABASE_URL, url_id):
    conn = psycopg2.connect(DATABASE_URL)
    # забираем новую запись о проверке с бд
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute("SELECT * FROM url_checks \
        WHERE url_id=%s ORDER BY check_id DESC", (url_id,))
        url_checks = curs.fetchall()
    conn.close()
    return url_checks


def db_add_check(DATABASE_URL, id, status_code, h1, title, description):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as curs:
        curs.execute(
            "INSERT INTO url_checks (url_id,"
            "status_code, h1, "
            "title, description,"
            "created_at)\
            VALUES (%s, %s, %s, %s, %s, %s);",
            (id, status_code, h1, title,
             description, date.today().isoformat()),
        )
    conn.commit()
    conn.close()
