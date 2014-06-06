
import os
import hashlib
import gluon.contenttype




def index():
    response.title = 'Gallery'
    galleries = db(db.gallery.creator == auth.user_id).select()
    for i in galleries:
        new_list=[]
        for each in i.photos:
            
            if db(db.vfile.id==each).select().first():
                new_list.append(each)
        i.update_record(photos=new_list)
                #print each
    return dict(galleries=galleries)

def show():
    '''Show a specefic gallery'''
    session.view        = 'gallery.show'
    session.description = 'Ourway gallery | Simply Share your photos online with your friends.'
    pcode          = request.vars.pcode
    if request.args:
        file = None
        gal_uuid   = urlbase = request.args[0]
        gallery    = db(db.gallery.uuid==gal_uuid).select().first()
        if len(request.args)>1:
            uuid_string=request.args[-1]
            file    = db(db.vfile.uuid==uuid_string).select().first()
            urlbase +=  uuid_string
            urlbase = hashlib.md5(urlbase).hexdigest()
        item = db(db.item.pid == urlbase).select().first()
        if not item:
             redirect(URL(r=request, c='error', f='index', vars={'_ref':'item deleted!'}))
        if pcode and pcode!=item.publish_code:
            redirect(URL(r=request, c='gallery', f='index', vars={'_ref':'pcode_Error'}))
        response.title = XML("Ourway ShowRoom&reg;")
        if item.description: response.title = XML('%s - Ourway ShowRoom&reg;' % item.description[:64])
        if gallery and file:
            return dict(gallery=gallery, file=file, item=item)

        elif gallery:
            #print urlbase
            return dict(gallery=gallery, item=item)
        else:
            redirect(URL(r=request, c='gallery', f='index', vars={'_ref':'error_args'}))
    else:
        redirect(URL(r=request, c='gallery', f='index', vars={'_ref':'no_args'}))

def update_file_desc():
    '''update description of a file in database - Ajax usage'''
    desc     = request.vars.file_desc_area
    pid = request.vars.pid
    item   = db(db.item.pid == pid).select().first()
    null = '<span style="color:#ccc;">Write Something About this photo</span>'
    if item:
        item.update_record(description=desc)
        if desc: return desc
        else: return null
    else:
        return null

def _download_photo():
    hash   = request.vars.hash #user downloads the file so no need to use UUID.
    filedb = db(db.vfile.hash==hash).select()
    if len(filedb):
        file = filedb[0]
        path = os.path.join(request.folder,'static/uploads', file.hash)
        if os.path.isfile(path):
            file_type= gluon.contenttype.contenttype(file.name)
            response.headers['Content-Type']       = file_type
            response.headers['Content-Disposition']= "attachment; filename=%s" % file.name
            return response.stream(path,1024*8)
            #return file_type

def _delete_photo():
    '''Delete a photo file by hash.'''
    uuid_string  = request.vars.uuid  #we want to delete a specefic file database, so we use uuid.
    gallery_uuid = request.vars.galuuid #delete it from spesefic gallery
    file     = db( db.vfile.uuid==uuid_string ).select().first()
    gallery  = db( (db.gallery.uuid==gallery_uuid) & (db.gallery.creator==session.user_id)).select().first()
    if gallery and file: #if both available
        new = []
        old = gallery.photos
        for i in old:
            if i != file.id: new.append(i)
        if file.id == gallery.artwork:
            gallery.update_record(photos = new, artwork=None)
        else:
            gallery.update_record(photos = new)
        item = db( (db.item.pid==hashlib.md5(gallery_uuid+uuid_string).hexdigest() ) & (db.item.owner == session.user_id) )
        item.delete()
    redirect('index')

def new_pic_ajax():
    return dict()

def upload_photos():
    gid     = request.vars.gid
    gallery = db(db.gallery.uuid==gid).select().first()
    #print gallery
    #print Auth.user_id
    #print auth.user_id==gallery.creator
    if gallery and auth.user_id==gallery.creator:
        return dict()
    else:
        redirect(URL(r=request, c='gallery', f='index', vars={'_ref':'error_args'}))

def delete_gallery():
    return dict(gid=request.vars.gid)

def delete_gallery_ajax():
    gid = request.vars.gid
    gallery = db( (db.gallery.uuid==gid) & (db.gallery.creator==session.user_id) )
    if gallery:
        return gallery.delete()

def create_new_gallery():
    return dict()

def create_new_gallery_ajax():
    name           =  request.vars.new_gal_name
    gallery     = db( (db.gallery.name==name) & (db.gallery.creator==auth.user_id) ).select().first()
    if not gallery and name:
        gallery = db.gallery.insert(name=name, photos=[])
        item    = db.item.insert(pid=gallery.uuid, type='gallery')
        #print item
        #print 'Done.'
        return 'Done.'
    else:
        return ''
