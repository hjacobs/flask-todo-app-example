#!/usr/bin/env python3
import os
from flask import Flask, redirect, url_for, render_template
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


@app.route("/")
def hello():
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    assert resp.ok
    return render_template("index.html", login=resp.json()["login"])


if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer

    address = "0.0.0.0", 8080
    server = WSGIServer(address, app)
    try:
        print("Server running on port %s:%d. Ctrl+C to quit" % address)
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
