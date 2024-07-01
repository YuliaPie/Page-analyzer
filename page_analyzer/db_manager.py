from datetime import date
from psycopg2.extras import NamedTupleCursor


def get_urls(conn):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
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
        all_urls = curs.fetchall()
    conn.close()
    return all_urls


def get_id_by_name(conn, name):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f"SELECT url_id FROM urls WHERE name='{name}'")
        url_id = curs.fetchone()
    conn.close()
    return url_id


def insert_url_get_id(conn, name):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        current_date = date.today().isoformat()
        curs.execute(f"""
        INSERT INTO urls (name, created_at)
        VALUES ('{name}', '{current_date}')
        RETURNING url_id;
        """)
        id = curs.fetchone().url_id
        conn.commit()
        conn.close()
        return id


def get_url_by_id(conn, id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f'SELECT * FROM urls WHERE url_id={id}')
        url = curs.fetchone()
        conn.close()
    return url


def get_checks_by_url_id(conn, url_id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f"""SELECT * FROM url_checks
        WHERE url_id={url_id} ORDER BY check_id DESC""")
        url_checks = curs.fetchall()
        conn.close()
    return url_checks


def insert_check(conn, id, status_code, h1, title, description):
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(f"""INSERT INTO url_checks (url_id,
        status_code, h1, title, description, created_at)
        VALUES ({id}, {status_code}, '{h1}', '{title}',
        '{description}', '{date.today().isoformat()}');""")
    conn.commit()
    conn.close()
