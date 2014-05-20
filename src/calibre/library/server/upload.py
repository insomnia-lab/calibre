#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__   = 'GPL v3'
__copyright__ = '2010, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import os
import cherrypy
import tempfile

from calibre.library.cli import do_add

def utf8(x):  # {{{
    if isinstance(x, unicode):
        x = x.encode('utf-8')
    return x
# }}}

class Endpoint(object):  # {{{
    'Manage encoding, mime-type '
    def __init__(self, mimetype='text/html; charset=utf-8'):
        self.mimetype = mimetype
       
    def __call__(eself, func):
        def do(self, *args, **kwargs):
            ans = func(self, *args, **kwargs)
            cherrypy.response.headers['Content-Type'] = eself.mimetype
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
        if not hasattr(self, '__upload_form_template__') or \
                self.opts.develop:
            self.__upload_form_template__ = \
                P('content_server/upload/form_bootstrap.html', data=True).decode('utf-8')
        
        ans = self.__upload_form_template__
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
        
        #copy file in tmp folder
        size = 0
        while True:
            data = book_file.file.read(8192)
            if not data:
                break
            os.write(tmpFile[0],data)
            size += len(data)
       
        #add book to library
        
        #   indirect way
        #   using command_add(list command_line_args, string library_path)
        #command_add([tmpFile[1]], self.opts.with_library)
        
        #   direct way   
        #   using do_add
        #   do_add(db, paths, one_book_per_directory, recurse, add_duplicates, otitle, oauthors, oisbn, otags, oseries, oseries_index, ocover)
        db = self.db
        do_add(db,[tmpFile[1]],False,False,False,book_file.filename,[book_author],None,["web_uploaded"],book_isbn,None,None)
        
        ans = out % (size, book_file.filename, book_file.content_type,book_file.filename,[book_author])
        
        os.close(tmpFile[0])
        os.remove(tmpFile[1])
        
        return ans
