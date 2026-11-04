import os
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)
DATABASE = "/tmp/lab.db"
VULNERABLE = os.getenv("LAB_MODE", "vulnerable") == "vulnerable"


def connection():
    db = sqlite3.connect(DATABASE)
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, role TEXT)")
    db.execute("INSERT OR IGNORE INTO users VALUES (1, 'student', 'player')")
    db.execute("INSERT OR IGNORE INTO users VALUES (2, 'mentor', 'admin')")
    db.commit()
    return db


@app.get("/search")
def search():
    username = request.args.get("username", "")
    db = connection()
    if VULNERABLE:
        rows = db.execute(f"SELECT id, username, role FROM users WHERE username = '{username}'").fetchall()
    else:
        rows = db.execute(
            "SELECT id, username, role FROM users WHERE username = ?",
            (username,),
        ).fetchall()
    return jsonify({"mode": "vulnerable" if VULNERABLE else "fixed", "results": rows})


@app.get("/health")
def health():
    return {"status": "ok", "mode": "vulnerable" if VULNERABLE else "fixed"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
