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

from django.utils import simplejson 

from db import ColorName

class saveWithSingleAPI(webapp.RequestHandler):
    def post(self):
        name = self.request.get('name')
        name_yomi = self.request.get('name_yomi')
        red = self.request.get('red')
        green = self.request.get('green')
        blue = self.request.get('blue')
        rank = self.request.get('rank')
        
        color_name = ColorName().all()\
                        .filter('name =', name)\
                        .filter('name_yomi =', name_yomi)\
                        .filter('red =', int(red))\
                        .filter('green =', int(green))\
                        .filter('blue =', int(blue))\
                        .get()
                        
        if color_name is None:
            color_name = ColorName()
            color_name.name = name
            color_name.name_yomi = name_yomi
            color_name.red = int(red)
            color_name.green = int(green)
            color_name.blue = int(blue)
        
        color_name.rank = int(rank)
        color_name.put()

        json = simplejson.dumps({'state': 'ok'}, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)
        
class saveWithMultipleAPI(webapp.RequestHandler):
    def post(self):
        raw_data = self.request.get('raw_data')
        
        if raw_data != '':
            json_data = simplejson.loads(raw_data)
            
            for data in json_data:
                name = data['name']
                name_yomi = data['name_yomi']
                red = data['red']
                green = data['green']
                blue = data['blue']
                rank = data['rank']
            
                color_name = ColorName().all()\
                                .filter('name =', name)\
                                .filter('name_yomi =', name_yomi)\
                                .filter('red =', red)\
                                .filter('green =', green)\
                                .filter('blue =', blue)\
                                .get()
                                
                if color_name is None:
                    color_name = ColorName()
                    color_name.name = name
                    color_name.name_yomi = name_yomi
                    color_name.red = int(red)
                    color_name.green = int(green)
                    color_name.blue = int(blue)
                
                color_name.rank = int(rank)
                color_name.put()

        json = simplejson.dumps({'state': 'ok'}, ensure_ascii=False)
        self.response.content_type = 'application/json'
        self.response.out.write(json)
        
class saveTestPage(webapp.RequestHandler):
    def get(self):
        
        data = []
        data.append({'name': 'name',
                     'name_yomi': 'name yomi',
                     'red': 10,
                     'green': 20,
                     'blue': 30,
                     'rank': 5})
        data.append({'name': 'name',
                     'name_yomi': 'name yomi',
                     'red': 20,
                     'green': 30,
                     'blue': 40,
                     'rank': 15})
        data.append({'name': 'name',
                     'name_yomi': 'name yomi',
                     'red': 50,
                     'green': 60,
                     'blue': 70,
                     'rank': 20})
        
        json_data = simplejson.dumps(data)
        
        template_values = {
            'json_data': json_data
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/api/save.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                     [('/api/v1/save_with_single', saveWithSingleAPI),
                                      ('/api/v1/save_with_multiple', saveWithMultipleAPI),
                                      ('/api/v1/save_test', saveTestPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()