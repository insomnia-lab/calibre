#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__   = 'GPL v3'
__copyright__ = '2010, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import operator, os, re, time
import cherrypy

#propirata import
import tempfile
from calibre.db.legacy import LibraryDatabase

from binascii import hexlify, unhexlify
from collections import OrderedDict
from calibre.constants import filesystem_encoding, config_dir
from calibre import (isbytestring, force_unicode, fit_image, prepare_string_for_xml, sanitize_file_name2)
from calibre.utils.filenames import ascii_filename
from calibre.utils.icu import sort_key
from calibre.utils.magick import Image
from calibre.library.comments import comments_to_html
from calibre.library.server import custom_fields_to_display
from calibre.library.field_metadata import category_icon_map
from calibre.library.server.utils import quote, unquote
from calibre.db.categories import Tag
from calibre.ebooks.metadata.sources.identify import urls_from_identifiers
from calibre.library.cli import command_add, do_add

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
#                sort_val = None
#                cookie = cherrypy.request.cookie
#                if eself.sort_cookie_name in cookie:
#                    sort_val = cookie[eself.sort_cookie_name].value
#                kwargs[eself.sort_kwarg] = sort_val
#
#            # Remove AJAX caching disabling jquery workaround arg
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
    
    #retrive html template from resource folder
    def upload_template(self):

        if not hasattr(self, '__browse_template__') or \
                self.opts.develop:
            self.__browse_template__ = \
                P('content_server/upload/form_bootstrap.html', data=True).decode('utf-8')
        
        ans = self.__browse_template__
        ans = ans.replace('{prefix}', self.opts.url_prefix)
        return ans
    
    @Endpoint()    
    def upload_form(self):        
        return self.upload_template()
    
    @Endpoint()
    def upload_bay(self, book_file, book_author, book_isbn):
        out = """
        <!DOCTYPE html>
        <html>
        <body>
            myFile length: %s<br />
            myFile filename: %s<br />
            myFile mime-type: %s<br />
            myFile title: %s<br />
            myFile authors: %s
        </body>
        </html>
        """
        
        tmp_bay_path="/tmp/calibre_bay"
        
        #create tmp directory for bay if not exists
        try:
           os.mkdir(tmp_bay_path)
        except OSError as err:
           pass
        else:
           print "Created tmp directory: "+tmp_bay_path
        
        #create tmp file
        tmpFile=tempfile.mkstemp("",book_file.filename+"_","/tmp/calibre_bay")
        
        tmpFileHandler=tmpFile[0]
        
        #copy file in tmp folder
        size = 0
        while True:
            data = book_file.file.read(8192)
            if not data:
                break
            os.write(tmpFileHandler,data)
            size += len(data)
        
        #add book to library
        
        #   indirect way
        #   using command_add(list command_line_args, string library_path)
        #command_add([tmpFile[1]], self.opts.with_library)
        #   direct way   
        #   using do_add
        #   do_add(db, paths, one_book_per_directory, recurse, add_duplicates, otitle, oauthors, oisbn, otags, oseries, oseries_index, ocover)
        db = get_db(self.opts.with_library)
        do_add(db,[tmpFile[1]],False,False,False,book_file.filename,[book_author],None,["web_uploaded"],book_isbn,None,None)
        return out % (size, book_file.filename, book_file.content_type,book_file.filename,[book_author])
        upload.exposed = True
        
def get_db(library_path):
    dbpath = os.path.expanduser(library_path)
    dbpath = os.path.abspath(dbpath)
    return LibraryDatabase(dbpath)
    
