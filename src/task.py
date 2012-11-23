# -*- coding: utf-8 -*-

import os
import hashlib
import logging
import uuid
import datetime

import webapp2
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import taskqueue

import png

from StringIO import StringIO

try:
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw
except ImportError:
    import Image
    import ImageFont
    import ImageDraw
    
from common import hex_to_rgb
from common import rgb_to_hex

from db import UserPrefs
from db import ColorName
from db import CrayonData

class CreateCrayonTask(webapp2.RequestHandler):
    def post(self):
        id = self.request.get('id')

        color_name = ColorName.get_by_id(int(id))
        if color_name is None:
            logging.error('color name not found.')
            return self.error(200)
        
        path = os.path.join(os.path.dirname(__file__), 'psd/layer02.png')
        
        pr = png.Reader(file=open(path, 'rb'))
        x,y,pixdata,meta = pr.asRGBA8()
        
        new_pixdata = []
        for pixcel in pixdata:
            i = 0
            new_p = []
            new_p_set = []
            for p in pixcel:
                new_p_set.append(p)
                i += 1
                if i >= 4:
                    if new_p_set == [255, 0, 0, 255]:
                        new_p_set = [color_name.red, color_name.green, color_name.blue, 255]
                    new_p.extend(new_p_set)
                    i = 0
                    new_p_set = []
            new_pixdata.append(new_p)
                    
        pw = png.Writer(
            x,
            y,
            interlace=False,
            bitdepth=meta['bitdepth'],
            planes=meta['planes'],
            alpha=True
        )
                    
        o = StringIO()
        pw.write(o, new_pixdata)
        new_image_binary_data = o.getvalue()
        layer02_image = images.Image(new_image_binary_data)
        
        path = os.path.join(os.path.dirname(__file__), 'psd/YasashisaBold.ttf')
        im = Image.new('RGBA', (562,168), (0,0,0,0))
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(path, 45)
        
        str = rgb_to_hex((color_name.red, color_name.green, color_name.blue))
        (w,h) = draw.textsize(str, font=font)
        
        draw.text(((562-w-60)/2, (168-h-13)/2), str, font=font, fill='rgb(0,0,0)')
        
        fio = StringIO()
        im.save(fio, "PNG")
        data = fio.getvalue()
        fio.close()
        
        layer03_image = images.Image(data)
        
        path = os.path.join(os.path.dirname(__file__), 'psd/layer01.png')
        layer01_image = images.Image(file(path, 'rb').read())
        
        all_images = []
        all_images.append((layer02_image, 0, 0, 1.0, images.TOP_LEFT))
        all_images.append((layer01_image, 0, 0, 1.0, images.TOP_LEFT))
        all_images.append((layer03_image, 0, 0, 1.0, images.TOP_LEFT))
            
        image_c = images.composite(all_images, 562, 168, 0, images.PNG, 100)
        img = images.Image(image_c)
        img.resize(width=320)
        result = img.execute_transforms(output_encoding=images.PNG)
            
        crayon_data = CrayonData.all().filter('color_name =', color_name).get()
        if crayon_data is None:
            logging.info('new data.')
            crayon_data = CrayonData()
        else:
            logging.info('saved data.')
            
        crayon_data.color_name = color_name
        crayon_data.image = db.Blob(result)
        crayon_data.put()
            

app = webapp2.WSGIApplication([('/task/create_crayon', CreateCrayonTask)])