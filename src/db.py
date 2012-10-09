# -*- coding: utf-8 -*-

from google.appengine.ext import db

class ColorName(db.Model):
    name = db.StringProperty()
    name_yomi = db.StringProperty()
    red = db.IntegerProperty()
    green = db.IntegerProperty()
    blue = db.IntegerProperty()
    rank = db.IntegerProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)