# -*- coding: utf-8 -*-

import string

from random import choice

def gen_userid(length=6, chars=string.letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])