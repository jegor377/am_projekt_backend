import mimetypes

from flask import Flask, g, send_file, abort
import sqlite3

DATABASE = './db.db'


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
    res.execute("SELECT * FROM movies WHERE id=:movie_id", {
        "movie_id": movie_id
    })

    movie = res.fetchone()

    if movie is None:
        return abort(404)

    movie_imgs = res.execute("SELECT * FROM imgs WHERE movie_id=:id", {
        "id": movie['id']
    }).fetchall()
    movie["imgs"] = movie_imgs

    return movie


@app.get("/movies")
def movies():
    db = get_db()
    res = db.cursor()
    res.execute("SELECT * FROM movies")

    return res.fetchall()


@app.get("/img/<string:name>")
def img(name):
    filepath = f"./imgs/{name}"
    mimetype, _ = mimetypes.guess_type(filepath)
    return send_file(filepath, mimetype=mimetype)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5100)