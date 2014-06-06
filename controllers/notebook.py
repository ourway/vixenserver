#Ourway Blogging system.
#Farsheed Ashouri
import urllib
import xmlrpclib
import gzip
import html2text as ht
import string
from encoding import smart_str, smart_unicode


@auth.requires_login()
def index():
    '''Blog'''
    response.title="%s %s's Notebook" % (auth.user.first_name.title(), auth.user.last_name.title())
    return response.render('notebook/index_mainpage.html')

def toolbar():
    '''ajaxload'''
    return dict()

def previews():
    '''ajaxload'''
    return dict()

def topics():
    '''ajaxload'''
    return dict()

def ajax_add():
    '''Load new note adding page and render it'''
    data = response.render('notebook/add.html')
    return data

def find_tags(body):
    sym = '@'
    tags = [tag for tag in body.split() if (tag[0] == sym and \
                len(tag)>1 and tag[1]!=sym)]
    return tags

def ajax_do_add():
    '''Load new note adding page and render it'''
    body = request.vars.body
    title = request.vars.title
    if body and title:
        tags =find_tags(body)
        note = db.note.insert(title=title, body=body)
        newlink = URL(f='note', vars={'nuuid':note.uuid})
        return '<h3>Thank you, Your new note is <a href="%s">here</a></h3>' % newlink

def note():
    '''show note'''
    nuuid = request.vars.nuuid
    note = db(db.note.uuid == nuuid).select().first()
    if note:
        body=note.body
        tags =find_tags(note.body)
        words = note.body.split()
        '''
        for tag in tags:
            word = tag.replace(tag, '[[\%s %s]]' % (tag, \
                URL(c='notebook', f='tags', vars={'tag':tag[1:]})) )
            body = body.replace(tag, word)

        '''
        return dict(title=note.title, body=body, tags=tags, nuuid=note.uuid, date=note.created)
    else:
        redirect(URL(f='index'))
        
    

