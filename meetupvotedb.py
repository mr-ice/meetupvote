from google.appengine.ext import db

class Voters (db.Model):
    site = db.StringProperty()
    voter = db.UserProperty()
    nick = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    votes = db.IntegerProperty()

class Places (db.Model):
    site = db.StringProperty()
    name = db.StringProperty()
    votes = db.IntegerProperty()
    addedby = db.ReferenceProperty(Voters)

class Cron (db.Model):
    minute = db.IntegerProperty()
    hour = db.IntegerProperty()
    dow = db.IntegerProperty()
    dom = db.IntegerProperty()
    url = db.StringProperty()

class Template (db.Model):
    site = db.StringProperty()
    name = db.StringProperty()
    url = db.StringProperty()
    to = db.StringProperty()
    from = db.StringProperty()
    subject = db.StringProperty()
    body = db.StringProperty()
