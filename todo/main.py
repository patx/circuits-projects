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


# Declare some constants for the database
HOST_URI = "ADD URI HERE"
client = MongoClient(HOST_URI)
db = client["todo"]


# Set up an environment for the jinja2 templates to be loaded from
env = Environment(loader=FileSystemLoader("templates"))

def render(name, **args):
    """Returns a formatted jinja2 template"""
    return env.get_template(name).render(args)


def add_item(content, tags):
    """Add and item to the database. Each document has content, tags, and
       an id. Returns True
    """
    item = {"content": content, "tags": tags.split(),
            "id": str(uuid4())}
    db.items.insert(item)
    return True


def matching_tags(tag):
    """Return all documenst with a tag matching the specified arg 
       (tag) in reverse order
    """
    matching_items = []
    for item in db.items.find():
        if tag in item["tags"]:
            matching_items.append(item)
    return matching_items[::-1]


def get_all_items():
    """Retrives all documents in the databaase and returns them in reverse 
       order
    """
    all_items = []
    for item in db.items.find():
        all_items.append(item)
    return all_items[::-1]


def get_all_tags():
    """Returns a list of every tag in the database"""
    all_tags = []
    for item in db.items.find():
        for each in item["tags"]:
            if each not in all_tags:
                all_tags.append(each)
    return all_tags


class Root(Controller):
    """
        circuits.web Controller class
        Request handlers for the appen
    """

    def index(self):
        """Index page, displays all todo items and all tags"""
        return render("index.html", seq=get_all_items(), tags=get_all_tags())

    def add(self, content=None, tags=None):
        """Request handler that only takes POST requests and adds documents"""
        if self.request.method == "POST":
            add_item(content=content, tags=tags)
            return self.redirect("/")

    def delete(self, id=None, redirect_tag=None):
        """Delete a document
           id --> the id of the document to be deleted
           redirect_tag --> if deleted from the tag page redirect back to same 
                            page
        """
        if id is not None:
            db.items.delete_one({"id": id})
        if redirect_tag:
            return self.redirect("/tag/{}".format(redirect_tag))
        else:
            return self.redirect("/")

    def tag(self, tag=None):
        """Display all documents that have the specified tag"""
        return render("tag.html", tag=tag, tag_items=matching_tags(tag))


class Auth(Component):
    """
        Auth class, creates http auth to protect the application from
        unwanted users, currently no signup/login feature. To add users you
        must edit the users dict below
    """

    realm = "ToDo App"
    users = {"USERNAME HERE": "PASSWORD HERE"}

    @handler("request", priority=1.0)
    def on_request(self, event, request, response):
        if not check_auth(request, response, self.realm, self.users):
            event.stop()
            return digest_auth(request, response, self.realm, self.users)


# Register Root() and Auth() to app (Server()) and run the app on port 5000
port = int(os.environ.get("PORT", 5000))
app = Server(("0.0.0.0", port))
Root().register(app)
Auth().register(app)
app.run()

