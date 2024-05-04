import mimetypes

from flask import Flask, g, send_file, abort
import sqlite3

DATABASE = './db.db'
PORT = 5100
IP = "192.168.5.63"
URL = f"http://{IP}:{PORT}"


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


@app.get("/movies")
def movies():
    db = get_db()
    res = db.cursor()
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
                "LEFT JOIN genres g ON (m.genre_id = g.id)")

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
    app.run(host="0.0.0.0", port=PORT)
