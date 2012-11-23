# -*- coding: utf-8 -*- 

import os
import logging
import datetime

import webapp2
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.api import mail

from db import ColorName
from db import UserPrefs
from db import CrayonData

class UserPage(webapp2.RequestHandler):
    def get(self, user_id):
        user_prefs = UserPrefs().all().filter('user_id =', user_id).get()
        
        if user_prefs is None:
            return self.error(404)
        
        color_name_list = ColorName.all()\
                            .filter('user_prefs =', user_prefs)\
                            .order('rank')\
                            .fetch(100, 0)
        
        color_list = []
        #color_list.append({'name': 'test',
        #                   'name_yomi': 'test',
        #                   'hex': '%02x%02x%02x' % (128,
        #                                             128,
        #                                             128)
        #                   })
        for color_name in color_name_list:
            is_crayon_available = CrayonData.all().filter('color_name =', color_name).get()
            color_list.append({'id': color_name.key().id(),
                               'name': color_name.name,
                               'name_yomi': color_name.name_yomi,
                               'is_crayon_available': True if is_crayon_available else False,
                               'hex': '%02x%02x%02x' % (color_name.red,
                                                         color_name.green,
                                                         color_name.blue)
                               })
        
        template_values = {
            'nick_name': user_prefs.nick_name,
            'user_id': user_prefs.user_id,
            'color_list': color_list
            
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/user.html')
        self.response.out.write(template.render(path, template_values))

app = webapp2.WSGIApplication(
                                     [('/([^/]+)', UserPage),])