# -*- coding: utf-8 -*-

from google.appengine.ext import db

class UserPrefs(db.Model):
    user_id = db.StringProperty()
    google_account = db.UserProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now_add=True)
    
class ColorName(db.Model):
    user_prefs = db.ReferenceProperty(UserPrefs)
    name = db.StringProperty()
    name_yomi = db.StringProperty()
    red = db.IntegerProperty()
    green = db.IntegerProperty()
    blue = db.IntegerProperty()
    rank = db.IntegerProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    