# -*- coding: utf-8 -*- 

import os
import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.api import mail

from db import ColorName
from db import UserPrefs

class UserPage(webapp.RequestHandler):
    def get(self, user_id):
        user_prefs = UserPrefs().all().filter('user_id =', user_id).get()
        
        if user_prefs is None:
            return self.error(404)
        
        color_name_list = ColorName.all()\
                            .filter('user_prefs =', user_prefs)\
                            .order('rank')\
                            .fetch(100, 0)
        
        color_list = []
        for color_name in color_name_list:
            color_list.append({'name': color_name.name,
                               'name_yomi': color_name.name_yomi,
                               'hex': '#%02x%02x%02x' % (color_name.red,
                                                         color_name.green,
                                                         color_name.blue)
                               })
        
        template_values = {
            'user_name': user_id,
            'color_list': color_list
            
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/user.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('/([^/]+)', UserPage),],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()