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
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.api import memcache

import json

from common import gen_userid

from db import ColorName
from db import UserPrefs
from db import CrayonData

class loginAPI(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            login_url = users.create_login_url('/api/v1/login?first=true')
            return self.redirect(login_url)
        
        continue_login = self.request.get('continue')
        first_login = self.request.get('first')
        
        user_id = gen_userid()
        
        user_prefs_query = UserPrefs().all()
        user_prefs_query.filter('google_account =', user)
        
        template_name = 'login.html'
        
        is_previously_saved = False
        user_prefs = user_prefs_query.get()
        if user_prefs is None:
            user_prefs = UserPrefs()
            user_prefs.user_id = user_id
            user_prefs.google_account = user
            user_prefs.put()
            
        else:
            color_name = ColorName.all().filter('user_prefs =', user_prefs).count(10)
            if color_name > 0:
                is_previously_saved = True
                
            if continue_login != 'true' and first_login != 'true':
                template_name = 'confirm_login.html'
        
        template_values = {
            'account': user.email(),
            'user_id': user_prefs.user_id,
            'avatar_available': True if user_prefs.avatar else False,
            'is_previously_saved': is_previously_saved
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/api/%s' % template_name)
        self.response.out.write(template.render(path, template_values))

class logoutAPI(webapp2.RequestHandler):
    def get(self):
        successful = self.request.get('successful')
        continue_login = self.request.get('continue')
        
        if continue_login == 'true':
            logout_url = users.create_logout_url('/api/v1/login')
            return self.redirect(logout_url)
        
        if successful != 'true':
            logout_url = users.create_logout_url('/api/v1/logout?successful=true')
            return self.redirect(logout_url)
        
        template_values = {
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/api/logout.html')
        self.response.out.write(template.render(path, template_values))

class saveWithSingleAPI(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        
        user_prefs_query = UserPrefs().all()
        user_prefs_query.filter('google_account =', user)
        
        user_prefs = user_prefs_query.get()
        
        if user is not None and user_prefs is not None:
            name = self.request.get('name')
            name_yomi = self.request.get('name_yomi')
            red = self.request.get('red')
            green = self.request.get('green')
            blue = self.request.get('blue')
            rank = self.request.get('rank')
            
            color_name = ColorName().all()\
                            .filter('user_prefs =', user_prefs)\
                            .filter('name =', name)\
                            .filter('name_yomi =', name_yomi)\
                            .filter('red =', int(red))\
                            .filter('green =', int(green))\
                            .filter('blue =', int(blue))\
                            .get()
                            
            if color_name is None:
                color_name = ColorName()
                color_name.user_prefs = user_prefs
                color_name.name = name
                color_name.name_yomi = name_yomi
                color_name.red = int(red)
                color_name.green = int(green)
                color_name.blue = int(blue)
            
            color_name.rank = int(rank)
            color_name.put()
            
            taskqueue.add(url='/task/create_crayon', params={'id': color_name.key().id()})
    
            data = json.dumps({'state': 'ok'}, ensure_ascii=False)
            
        else:
            data = json.dumps({'state': 'failed'}, ensure_ascii=False)
            
        self.response.content_type = 'application/json'
        self.response.out.write(data)
        
class saveWithMultipleAPI(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        
        user_prefs_query = UserPrefs().all()
        user_prefs_query.filter('google_account =', user)
        
        user_prefs = user_prefs_query.get()
        
        if user is not None and user_prefs is not None:
            raw_data = self.request.get('raw_data')
            
            if raw_data != '':
                json_data = json.loads(raw_data)
                
                saved_color_name_list = ColorName().all()\
                                    .filter('user_prefs =', user_prefs)\
                                    .fetch(100, 0)
                                    
                for saved_color_name in saved_color_name_list:
                    is_saved = False
                    for data in json_data:
                        if data['name'] == saved_color_name.name and \
                            data['red'] == saved_color_name.red and \
                            data['green'] == saved_color_name.green and \
                            data['blue'] == saved_color_name.blue:
                            
                            is_saved = True
                            continue
                        
                    if is_saved == False:
                        logging.info('delete.')
                        saved_color_name.delete()
                    else:
                        logging.info('not delete.')
                
                new_color_name_list = []
                
                for data in json_data:
                    name = data['name']
                    name_yomi = data['name_yomi']
                    red = data['red']
                    green = data['green']
                    blue = data['blue']
                    rank = data['rank']
                
                    color_name = ColorName().all()\
                                    .filter('user_prefs =', user_prefs)\
                                    .filter('name =', name)\
                                    .filter('name_yomi =', name_yomi)\
                                    .filter('red =', red)\
                                    .filter('green =', green)\
                                    .filter('blue =', blue)\
                                    .get()
                                    
                    do_create_crayon = False
                    if color_name is None:
                        color_name = ColorName()
                        color_name.user_prefs = user_prefs
                        color_name.name = name
                        color_name.name_yomi = name_yomi
                        color_name.red = int(red)
                        color_name.green = int(green)
                        color_name.blue = int(blue)
                        
                        new_color_name_list.append({'name': color_name.name,
                                   'name_yomi': color_name.name_yomi,
                                   'red': color_name.red,
                                   'green': color_name.green,
                                   'blue': color_name.blue})
                        
                        do_create_crayon = True
                    
                    color_name.rank = int(rank)
                    color_name.put()
                    
                    if do_create_crayon:
                        taskqueue.add(url='/task/create_crayon', params={'id': color_name.key().id()})
    
            data = json.dumps({'state': 'ok',
                               'user_id': user_prefs.user_id,
                               'new_color': new_color_name_list}, ensure_ascii=False)
            
        else:
            self.response.set_status(401)
            data = json.dumps({'state': 'failed'}, ensure_ascii=False)
            
        self.response.content_type = 'application/json'
        self.response.out.write(data)
        
class saveTestPage(webapp2.RequestHandler):
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
        
        json_data = json.dumps(data)
        
        template_values = {
            'json_data': json_data
        }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/api/save.html')
        self.response.out.write(template.render(path, template_values))

class showCrayonAPI(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('id')
        
        cache_key = 'cached_image_%s' % id
        
        image = memcache.get(cache_key)
        if image is None:
            color_name = ColorName.get_by_id(int(id))
            if color_name is None:
                return self.error(404)
            
            crayon_data = CrayonData.all().filter('color_name =', color_name).get()
            if crayon_data is None:
                return self.error(404)
            
            image = crayon_data.image
            
            memcache.add(cache_key, image, 3600)
            
            logging.info('create cache.')
        else:
            logging.info('load cache.')
            
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(image)
        
class showAvatarAPI(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('id')
        
        cache_key = 'cached_avatar_image_%s' % id
        
        image = memcache.get(cache_key)
        if image is None:
            user_prefs = UserPrefs.all().filter('user_id =', id).get()
            if user_prefs is None:
                return self.error(404)
            
            image = user_prefs.avatar
            
            memcache.add(cache_key, image, 3600)
            
            logging.info('create cache.')
        else:
            logging.info('load cache.')
            
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(image)
        
class updateProfileAPI(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        
        user_prefs_query = UserPrefs().all()
        user_prefs_query.filter('google_account =', user)
        
        user_prefs = user_prefs_query.get()
        
        if user is not None and user_prefs is not None:
            nick_name = self.request.get('nick_name')
            user_id = self.request.get('user_id')
            avatar = self.request.get('avatar')
            
            is_id_available = True
            id_check = UserPrefs.all().filter('user_id =', user_id).get()
            if id_check is not None:
                if id_check.google_account != user:
                    is_id_available = False
                    
            avatar_result = images.resize(db.Blob(avatar), 300, 300, output_encoding=images.PNG)
                    
            if is_id_available:
                user_prefs.user_id = user_id
                user_prefs.nick_name = nick_name
                user_prefs.avatar = db.Blob(avatar_result)
                user_prefs.put()
                
                data = json.dumps({'state': 'ok', 'user_id': user_prefs.user_id}, ensure_ascii=False)
            
            else:
                logging.info('nick name is not available.')
                
                self.response.set_status(401)
                data = json.dumps({'state': 'nick name is not available.'}, ensure_ascii=False)
            
        else:
            logging.info('unauthorized.')
            
            self.response.set_status(401)
            data = json.dumps({'state': 'failed'}, ensure_ascii=False)
            
        self.response.content_type = 'application/json'
        self.response.out.write(data)
        
class getFavoriteColorAPI(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        
        user_prefs_query = UserPrefs().all()
        user_prefs_query.filter('google_account =', user)
        
        user_prefs = user_prefs_query.get()
        
        if user is not None and user_prefs is not None:
            color_name_list = ColorName.all().filter('user_prefs =', user_prefs).fetch(100)
            color_list = []
            for color_name in color_name_list:
                color_list.append({'name': color_name.name,
                                   'name_yomi': color_name.name_yomi,
                                   'red': color_name.red,
                                   'green': color_name.green,
                                   'blue': color_name.blue,
                                   'rank': color_name.rank})
                
            data = json.dumps(color_list, ensure_ascii=False)
            
        else:
            self.response.set_status(401)
            data = json.dumps({'state': 'failed'}, ensure_ascii=False)
            
        self.response.content_type = 'application/json'
        self.response.out.write(data)
        
app = webapp2.WSGIApplication([('/api/v1/login', loginAPI),
                                      ('/api/v1/logout', logoutAPI),
                                      ('/api/v1/save_with_single', saveWithSingleAPI),
                                      ('/api/v1/save_with_multiple', saveWithMultipleAPI),
                                      ('/api/v1/get_favorite_color', getFavoriteColorAPI),
                                      ('/api/v1/show_crayon', showCrayonAPI),
                                      ('/api/v1/show_avatar', showAvatarAPI),
                                      ('/api/v1/update_profile', updateProfileAPI),
                                      ('/api/v1/save_test', saveTestPage)])