# meetupvote - a google apps engine tool for voting on meetups
# Copyright (C) 2010-2014 Michael Rice <michael@riceclan.org>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import cgi
import random

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import dinnerdb

def render(page,values):
    return template.render(os.path.join(os.path.dirname(__file__),page),values)

class MainPage (webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))

        me = dinnerdb.Voters.all().filter("voter =",user).get()
        if not me:
            self.redirect("/init")
        places = dinnerdb.Places.gql("ORDER BY votes DESC, name ASC")

        if self.request.get('vote'):
            if me.votes:
                me.votes = me.votes - 1
                if me.votes < 0: me.votes = 0
                me.put()
                voted = dinnerdb.db.get(self.request.get('vote'))
                voted.votes = voted.votes + 1
                voted.put()

        template_values = {
            'me' : me,
            'places': places,
            'logout': users.create_logout_url('/'),
            'admin': users.is_current_user_admin(),
            }
        self.response.out.write(render('index.html',template_values))
       
class EditLocations (webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        me = dinnerdb.Voters.all().filter('voter =',user).get()
        places = dinnerdb.Places.all().order('name')
        errormsg = None

        if self.request.get('deleteid'):
            deleted = dinnerdb.db.get(self.request.get('deleteid'))
            if deleted.votes == 0:
                deleted.delete()

            else:
                errormsg = "Cannot delete entry with votes"

        if self.request.get('new'):
            new = self.request.get('new')
            dinnerdb.Places(
                name = new,
                votes = 0,
                addedby = me,
                ).put()

        template_values = {
            'places': places,
            'request': self.request.get('deleteid'),
            'new' : self.request.get('new'),
            'errormsg': errormsg,
            }

        self.response.out.write(render('places.html',template_values))

class EditCron (webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        crontab = dinnerdb.Cron.all()

        template_values = {
            'crontab': crontab,
            }

        self.response.out.write(render('adminCron.html',template_values))

class EditVotes (webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        voters = dinnerdb.Voters.all()

        if self.request.get('to'):
            to = dinnerdb.db.get(self.request.get('to'))
            if self.request.get('add') == "5":
                to.votes = to.votes + 5
            else:
                to.votes = to.votes + 1
            to.put()
        if self.request.get('zero'):
            to = dinnerdb.db.get(self.request.get('zero'))
            to.votes = 0
            to.put()

        template_values = {
            'voters': voters,
            }

        self.response.out.write(render('adminVotes.html',template_values))

class InitVoter (webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        me = dinnerdb.Voters.gql("WHERE voter = :1",user).get()
        new = 0

        if not me:
            me = dinnerdb.Voters(
                        voter = users.get_current_user(),
                        nick = users.get_current_user().nickname(),
                        votes=0,
                        )
            me.put()
            new = 1

        if self.request.get('nick'):
            me.nick = self.request.get('nick')
            me.put()
        if self.request.get('Save'):
            self.redirect('/')

        template_values = {
            'me': me,
            'new': new,
            }
        self.response.out.write(render('setup.html',template_values))

class Reminder (webapp.RequestHandler):
    def get(self):
        print 'Content-type: text/plain'
        print ''
        sender = 'dndgeekout@dndgeekout.appspotmail.com'
        to = 'dndgeeks@googlegroups.com'
        subject = 'Remember to vote for Dinner'
        body = """
Visit http://dndgeekout.appspot.com/ to vote for your favorite dinner
locations.  If you are signing up for the first time email michael to
get an initial 5 votes.   Every time you show up to dinner with the 
group you will get 5 more votes.

The winning location is picked each Thursday at 3p and automatically mailed to
the group.  In cases of a tie the winner is picked randomly from all those with
the highest votes. 

All votes on the winning location are reset to zero.
"""
        mail.send_mail(sender,to,subject,body)

class ReminderCancelled (webapp.RequestHandler):
    def get(self):
        print 'Content-type: text/plain'
        print ''
        sender = 'dndgeekout@dndgeekout.appspotmail.com'
        to = 'dndgeeks@googlegroups.com'
        subject = 'No Dinner voting this week'
        body = """
No dinner votes this week, see ya'll next time.
"""
        mail.send_mail(sender,to,subject,body)

class PickWinnerCancelled (webapp.RequestHandler):
    def get(self):
        # null op here
        return

class PickWinner (webapp.RequestHandler):
    def get(self):
        max = dinnerdb.Places.all().order("-votes").get()
        if max.votes == 0:
            self.response.out.write('No votes, skipping dinner?')
        else:
            places = dinnerdb.Places.all().filter('votes =',max.votes).fetch(10)
            print 'Content-type: text/plain'
            print ''
            if places.count > 1:
                places = random.choice(places)
            sender = "dndgeekout@dndgeekout.appspotmail.com"
            to = "dndgeeks@googlegroups.com"
            subject = "Dinner Tonight at %s" % places.name
            body = """
The votes are in, the cheating is over, you voted (or not) and the result is

     %s with %d votes

Dinner tonight is at %s, per usual custom be there by 6 or you may be
eating alone.

""" % ( places.name,places.votes,places.name )

            places.votes = 0;
            places.put()
            mail.send_mail(sender,to,subject,body)
        
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/add', EditLocations),
                                      ('/adminVotes', EditVotes),
                                      ('/adminCron', EditCron),
                                      ('/adminTemplates', EditTemplates),
                                      ('/mail', PickWinner),
                                      ('/nomail', PickWinnerCancelled),
                                      ('/reminder',Reminder),
                                      ('/noreminder',ReminderCancelled),
                                      ('/init', InitVoter)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
