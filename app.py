import mimetypes

from flask import Flask, g, send_file, abort
import sqlite3
from dateutil.relativedelta import relativedelta
from datetime import datetime

DATABASE = './db.db'
PORT = 5100
IP = "192.168.5.63"
URL = f"https://{IP}:{PORT}"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = dict_factory
    return db


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


app = Flask(__name__)


@app.get("/movie_details/<int:movie_id>")
def movie_details(movie_id=0):
    db = get_db()
    res = db.cursor()
    res.execute(
        "SELECT m.id, g.name as genre, m.description, m.poster_url, m.release_date, m.title, m.trailer_yt_id FROM movies m LEFT JOIN genres g ON (m.genre_id = g.id) WHERE m.id=:movie_id",
        {
            "movie_id": movie_id
        })

    movie = res.fetchone()

    if movie is None:
        return abort(404)

    movie_imgs = res.execute("SELECT url, is_local FROM imgs WHERE movie_id=:id", {
        "id": movie['id']
    }).fetchall()
    movie["imgs"] = [img['url'] if img['is_local'] == 0 else f"{URL}{img['url']}" for img in movie_imgs]

    return movie


@app.get("/movies/<int:year>/<int:month>")
def movies(year, month):
    db = get_db()
    res = db.cursor()

    year_str = str(year).zfill(4)
    month_str = str(month).zfill(2)


    if month != 0:
        selected_date = datetime.strptime(f"{year_str}-{month_str}-01", "%Y-%m-%d")
        selected_date_str = selected_date.strftime("%Y-%m-%d")
        next_month_date = selected_date + relativedelta(months=1)
        next_month_date_str = next_month_date.strftime("%Y-%m-%d")
        condition = f"WHERE date(release_date) >= date('{selected_date_str}') AND date(release_date) < date('{next_month_date_str}')"
    else:
        selected_date = datetime.strptime(f"{year_str}-01-01", "%Y-%m-%d")
        selected_date_str = selected_date.strftime("%Y-%m-%d")
        next_year_date = selected_date + relativedelta(years=1)
        next_year_date_str = next_year_date.strftime("%Y-%m-%d")
        condition = f"WHERE date(release_date) >= date('{selected_date_str}') AND date(release_date) < date('{next_year_date_str}')"

    print(condition)

    res.execute("SELECT "
                "m.id,"
                "m.title,"
                "g.name as genre,"
                "(CASE WHEN length(m.description) > 512 THEN "
                "(substr(m.description, 0, 512) || '...' ) "
                "ELSE "
                "m.description "
                "END) as description,"
                f"('{URL}' || m.poster_url) as poster_url,"
                "m.release_date"
                " FROM movies m "
                "LEFT JOIN genres g ON (m.genre_id = g.id) "
                + condition)

    return res.fetchall()


@app.get("/img/<string:movie_id>/<string:name>")
def img(movie_id, name):
    filepath = f"./imgs/{movie_id}/{name}"
    mimetype, _ = mimetypes.guess_type(filepath)
    return send_file(filepath, mimetype=mimetype)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=PORT, ssl_context="adhoc")
