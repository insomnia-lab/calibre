#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__   = 'GPL v3'
__copyright__ = '2010, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import operator, os, json, re, time
from binascii import hexlify, unhexlify
from collections import OrderedDict

import cherrypy

from calibre.constants import filesystem_encoding, config_dir
from calibre import (isbytestring, force_unicode, fit_image,
        prepare_string_for_xml, sanitize_file_name2)
from calibre.utils.filenames import ascii_filename
from calibre.utils.config import prefs, JSONConfig
from calibre.utils.icu import sort_key
from calibre.utils.magick import Image
from calibre.library.comments import comments_to_html
from calibre.library.server import custom_fields_to_display
from calibre.library.field_metadata import category_icon_map
from calibre.library.server.utils import quote, unquote
from calibre.db.categories import Tag
from calibre.ebooks.metadata.sources.identify import urls_from_identifiers


def utf8(x):  # {{{
    if isinstance(x, unicode):
        x = x.encode('utf-8')
    return x
# }}}

class Endpoint(object):  # {{{
    'Manage encoding, mime-type, last modified, cookies, etc.'

    def __init__(self, mimetype='text/html; charset=utf-8', sort_type='category'):
        self.mimetype = mimetype
        self.sort_type = sort_type
        self.sort_kwarg = sort_type + '_sort'
        self.sort_cookie_name = 'calibre_browse_server_sort_'+self.sort_type

    def __call__(eself, func):

        def do(self, *args, **kwargs):
#            if 'json' not in eself.mimetype:
 #               sort_val = None
#                cookie = cherrypy.request.cookie
 #               if eself.sort_cookie_name in cookie:
#                    sort_val = cookie[eself.sort_cookie_name].value
 #               kwargs[eself.sort_kwarg] = sort_val
#
 #           # Remove AJAX caching disabling jquery workaround arg
#            kwargs.pop('_', None)

            ans = func(self, *args, **kwargs)
            cherrypy.response.headers['Content-Type'] = eself.mimetype
            updated = self.db.last_modified()
            cherrypy.response.headers['Last-Modified'] = \
                self.last_modified(max(updated, self.build_time))
            ans = utf8(ans)
            return ans

        do.__name__ = func.__name__

        return do
# }}}

class UploadServer(object):

    def add_routes(self, connect):
        base_href = '/upload'
        connect('upload_form', base_href+'/form', self.upload_form)
        connect('upload_bay', base_href+'/bay', self.upload_bay)

        #self.icon_map = JSONConfig('gu"i').get('tags_browser_category_icons', {})
    @Endpoint()    
    def upload_form(self):
        return """<!DOCTYPE html>
        <html>
        <body>
        <h2>Upload a file</h2>
        <form action="bay" method="post" enctype="multipart/form-data"> filename: <input type="file" name="book_file" /><br /><input type="submit" />
        </body></html>"""
    
    @Endpoint()
    def upload_bay(self, book_file):
        out = """
        <!DOCTYPE html>
        <html>
        <body>
            myFile length: %s<br />
            myFile filename: %s<br />
            myFile mime-type: %s
        </body>
        </html>
        """
        #from calibre.utils.config import prefs
        #from calibre.library.cli import command_add
        #book_file_name = ''
        #tmp_dir = tempfile.mkdtemp()
        #tmp_file = os.path.join(tmp_dir, book_file_name)
        #with open(tmp_file, 'w+') as f:
        #    while True:
        #       f.write(book_file.file.read(8192))
        #        if not data:
        #            break
        #command_add(tmp_file, prefs['library_path'])
        #return {}
        size = 0
        while True:
            data = book_file.file.read(8192)
            if not data:
                break
            size += len(data)
        return out % (size, book_file.filename, book_file.content_type)
        upload.exposed = True

    

