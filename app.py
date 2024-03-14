from flask import Flask, g
import sqlite3

DATABASE = './db.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


app = Flask(__name__)

@app.get("/movie_details/<int:movie_id>")
def movie_details(movie_id=0):
    return {
        "a": 1,
        "b": movie_id
    }


@app.get("/movies")
def movies():
    return [
        {"a": 1, "b": 3},
        {"a": 2, "b": 4},
        {"a": 3, "b": 5}
    ]


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
