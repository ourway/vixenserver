import xmlrpclib
import gzip
import html2text as ht
import urllib
import string


#import httpagentparser #a module for detecting browser type.

def _getfull_host():
    result = '%s://%s' % (request.env.wsgi_url_scheme, request.env.http_host)
    return result

def get_server():
    '''Returns XML-RPC server'''
    server_url          = _getfull_host() + URL(r=request, c='utils', f='call', args='xmlrpc')
    server=xmlrpclib.ServerProxy(server_url)
    return server

def get_visitors(pid):
    '''get visitor numbers by pid of item'''
    item=db(db.item.pid==pid).select().first()
    visitor=db((db.visitor.ip==request.env.remote_addr) & (db.visitor.item==item)).select().first()
    if not item: item=db.item.insert(pid=pid) #create new item
    if not visitor: visitor=db.visitor.insert(item=item) #add visitor to list
    nv=db(db.visitor.item==item).count() #count all visitors of this item
    return nv


def farsheed():
    '''My own resume and biography'''

    nv = get_visitors('pages.farsheed')
    session.keywords   = "social, network, ourway, about, co-founder,farshid, farsheed, ashouri, corp, فرشید, عاشوری, آشوری"
    response.title = "résumé - Farsheed (Farshid) Ashouri - Animator, VFX Artist and Software Entrepreneur"
    session.description = '''Farsheed (Farshid) Ashouri is a Senior Software Design Engineer in tehran. He is a Bachelor of Electronics from University of tabriz, and an Autodesk Certified. His professional domains of interest are System Architectures, entrepreneurship, Visual Effects, Computer Graphics, Animation and product management.'''
    #return response.render('generic.pdf')
    return dict(nv=nv)
