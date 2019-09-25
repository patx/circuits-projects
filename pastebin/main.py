# -*- coding: utf-8 -*-
"""circuits-pastebin

    A simple no frills pastebin using circuits.web, jinja2, pygments, and
    pymongo. It was written by Harrison Erd.
    https://patx.github.io
    http://circuits-pastebin.herokuapp.com
"""

import os
from uuid import uuid4

from circuits.web import Controller, Server
from jinja2 import Environment, FileSystemLoader
from pymongo import MongoClient
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.formatters import HtmlFormatter


HOST_URI = "URI HERE"
client = MongoClient(HOST_URI)
db = client.pastebin

env = Environment(loader=FileSystemLoader("templates"))


def render_template(name, **args):
    return env.get_template(name).render(args)


def get_paste(pid, line_numbers=None):
    for paste in db.pastes.find({"paste_id": pid}):
        code = paste["paste_content"]
        return highlight(code, guess_lexer(code), HtmlFormatter())


class Root(Controller):

    def GET(self, paste_id=None):
        if paste_id == "about":
            return render_template("about.html")
        if paste_id == None:
            return render_template("index.html")
        else:
            return render_template("paste.html", paste_id=paste_id,
              paste_content=get_paste(paste_id))

    def POST(self, paste_content):
        pid = str(uuid4())
        db.pastes.insert({"paste_id": pid, "paste_content": paste_content})
        return self.redirect("/{0}".format(pid))


(Server(("0.0.0.0", int(os.environ.get('PORT', 5000)))) + Root()).run()

