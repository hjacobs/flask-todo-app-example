#!/usr/bin/env python3
from gevent import monkey  # noqa

monkey.patch_all()  # noqa

import os
import logging
import functools
import redis
from flask import Flask, redirect, url_for, render_template, request
from werkzeug.contrib.fixers import ProxyFix
from flask_dance.contrib.github import make_github_blueprint, github

SECRET_KEY = os.getenv("SECRET_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = SECRET_KEY

blueprint = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
)
app.register_blueprint(blueprint, url_prefix="/login")

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_timeout=5)


def redirect_and_authorize(function):
    """redirect to login page unless logged in, redirect to canonical URL"""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        user = None
        if blueprint.session.authorized:
            try:
                response = github.get("/user")

                if response.status_code == 200:
                    user = response.json()
            except Exception as e:
                logging.info("Call to user info failed: %s", e)
        if not user:
            return redirect(url_for("github.login"))

        kwargs["login"] = user["login"]

        return function(*args, **kwargs)

    return wrapper


def get_redis_key(login):
    return "todo:{}:items".format(login)


@app.route("/")
@redirect_and_authorize
def index(login):
    items = []
    items_done = 0
    for x in r.lrange("todo:{}:items".format(login), 0, -1):
        s = x.decode("utf-8")
        item = {"text": s, "done": False}
        # this is a pretty hacky way of marking items as "done"
        if s.endswith(" - DONE"):
            item["text"] = s.rsplit(" - ")[0]
            item["done"] = True
            items_done += 1
        items.append(item)
    return render_template(
        "index.html", login=login, items=items, items_done=items_done
    )


@app.route("/add", methods=["POST"])
@redirect_and_authorize
def add(login):
    text = str(request.form["text"])
    logging.info("Adding as to-do for {}: {}".format(login, text))
    r.rpush(get_redis_key(login), text)
    return redirect("/")


@app.route("/delete/<int:id>", methods=["POST"])
@redirect_and_authorize
def delete(id, login):
    logging.info("Removing to-do #{} for {}".format(id, login))
    r.lset(get_redis_key(login), id, "DELETED")
    r.lrem(get_redis_key(login), 0, "DELETED")
    return redirect("/")


@app.route("/done/<int:id>", methods=["POST"])
@redirect_and_authorize
def done(id, login):
    logging.info("Marking to-do #{} as done for {}".format(id, login))
    text = r.lindex(get_redis_key(login), id)
    r.lset(get_redis_key(login), id, "{} - DONE".format(text.decode("utf-8")))
    return redirect("/")


@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer

    logging.basicConfig(level=logging.INFO)

    address = "0.0.0.0", 8080
    server = WSGIServer(address, app)
    try:
        print("Server running on port %s:%d. Ctrl+C to quit" % address)
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
