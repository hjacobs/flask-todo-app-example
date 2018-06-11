#!/usr/bin/env python3
import os
import redis
from flask import Flask, redirect, url_for, render_template, request
from werkzeug.contrib.fixers import ProxyFix
from flask_dance.contrib.github import make_github_blueprint, github

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = "supersekrit"

blueprint = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
)
app.register_blueprint(blueprint, url_prefix="/login")

r = redis.StrictRedis(host="localhost", port=6379, db=0)


@app.route("/")
def index():
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    assert resp.ok
    login = resp.json()["login"]
    items = r.lrange("todo:{}:items".format(login), 0, -1)
    return render_template("index.html", login=login, items=items)


@app.route("/add", methods=["POST"])
def add():
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    assert resp.ok
    login = resp.json()["login"]
    text = request.form["text"]
    print("Adding as to-do for {}: {}".format(login, text))
    r.rpush("todo:{}:items".format(login), text)
    return redirect("/")


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    assert resp.ok
    login = resp.json()["login"]
    r.lset("todo:{}:items".format(login), id, "DELETED")
    r.lrem("todo:{}:items".format(login), 0, "DELETED")
    return redirect("/")


if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer

    address = "0.0.0.0", 8080
    server = WSGIServer(address, app)
    try:
        print("Server running on port %s:%d. Ctrl+C to quit" % address)
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
