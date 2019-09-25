# -*- coding: utf-8 -*-

# ToDo Application by Harrison Erd using circuits.web, jinja2, and pymongo

import os
from time import strftime, gmtime
from uuid import uuid4

from circuits import Component, handler
from circuits.web import Server, Controller
from circuits.web.tools import check_auth, digest_auth
from jinja2 import Environment, FileSystemLoader
from pymongo import MongoClient


HOST_URI = "KEY HERE"
client = MongoClient(HOST_URI)
db = client["todo"]

env = Environment(loader=FileSystemLoader("templates"))


def render(name, **args):
    return env.get_template(name).render(args)


def add_item(content, tags):
    item = {"content": content, "tags": tags.split(),
            "id": str(uuid4())}
    db.items.insert(item)
    return True


def matching_tags(tag):
    matching_items = []
    for item in db.items.find():
        if tag in item["tags"]:
            matching_items.append(item)
    return matching_items[::-1]


def get_all_items():
    all_items = []
    for item in db.items.find():
        all_items.append(item)
    return all_items[::-1]


def get_all_tags():
    all_tags = []
    for item in db.items.find():
        for each in item["tags"]:
            if each not in all_tags:
                all_tags.append(each)
    return all_tags


class Root(Controller):

    def index(self):
        return render("index.html", seq=get_all_items(), tags=get_all_tags())

    def add(self, content=None, tags=None):
        if self.request.method == "POST":
            add_item(content=content, tags=tags)
            return self.redirect("/")

    def delete(self, id=None):
        if id is not None:
            db.items.delete_one({"id": id})
        return self.redirect("/")

    def tag(self, tag=None):
        return render("tag.html", tag=tag, tag_items=matching_tags(tag))


class Auth(Component):

    realm = "ToDo App"
    users = {"USERNAME HERE": "PASSWORD HERE"}

    @handler("request", priority=1.0)
    def on_request(self, event, request, response):
        if not check_auth(request, response, self.realm, self.users):
            event.stop()
            return digest_auth(request, response, self.realm, self.users)

port = int(os.environ.get("PORT", 5000))
app = Server(("0.0.0.0", port))
Root().register(app)
Auth().register(app)
app.run()

