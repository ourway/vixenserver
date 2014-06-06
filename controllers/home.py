admin_pass = 'VvisBlow'

import uuid
import os
import hashlib
import base64
import shutil
from subprocess import Popen, PIPE, call  # everything nedded to handle external commands
import cStringIO
import gluon.contenttype
from PyQRNative import *
import sys
import cairo
import pycha.pie
import time


def _getfull_host():
    result = '%s://%s' % (request.env.wsgi_url_scheme, request.env.http_host)
    return result


def piechart(data, title="Activity"):
    '''Draw pie chart from a data like this:
        data = (
          ('bar', 1),
          ('chart', 1),
          ('color', 1),
          ('line', 5),
          ('pie', 1),
          ('scatter', 4),
          )
        and return a vfile db of it.
    '''
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 800)

    dataSet = [(line[0], [[0, line[1]]]) for line in data]

    options = {
        'axis': {
            'x': {
                'ticks': [dict(v=i, label=d[0]) for i, d in enumerate(data)],
            }
        },
        'legend': {
            'hide': False,
        },
        'title': title,
    }
    chart = pycha.pie.PieChart(surface, options)

    chart.addDataset(dataSet)
    chart.render()

    ### write to disk
    upload_folder = '%sstatic/uploads' % request.folder
    fid = uuid.uuid4()
    output = '%s/%s.png' % (upload_folder, fid)
    surface.write_to_png(output)
    if os.path.isfile(output) and os.path.getsize(output):  # if file is available
        newfile = db.vfile.insert(uuid=uuid.uuid4(), name=os.path.basename(output), ext='png')
        return newfile


def qrcode(url):
    upload_folder = '%sstatic/uploads' % request.folder
    if not os.path.isdir(upload_folder):
        os.makedirs(upload_folder)
    qr = QRCode(6, QRErrorCorrectLevel.L)
    qr.addData(url)
    qr.make()
    im = qr.makeImage()
    fid = uuid.uuid4()
    newqrname = '%s/%s.png' % (upload_folder, fid)
    im.save(newqrname)
    if os.path.isfile(newqrname):
        newqr = db.vfile.insert(name=os.path.basename(newqrname), ext='png')

        return newqr


def about():
    response.title = 'About Vixen Server'
    return dict()


@auth.requires_login()
def index():
    '''Main intro page'''

    ############################################
    groups = ['master', 'managers', 'members', 'guests']
    for group in groups:
        if not db(db.auth_group.role==group).select().first():
            ng = auth.add_group(group, group)
            if group == 'master':
                auth.add_membership(ng, 1)
                
    
    

    ############################################



    response.title = "Rozaneh Production Asset Management System - Version 0.2.5"
    return dict()


def process(execfn):
    '''General external process'''
    p = Popen(execfn, shell=True, env=os.environ, stdout=PIPE, universal_newlines=True)  # process
    output = p.stdout.read()
    #print execfn
    p.wait()
    return output


def sha1sum(path):
    '''Find sha1sum of a file'''
    if os.path.isfile(path):
        arg = 'sha1sum "%s"' % path
        shafull = process(arg)
        if shafull:
            sha1sum = shafull.split()[0]
            return sha1sum


def check_permission():
    '''get the level of permission for a user'''
    if auth.has_membership('master', auth.user_id):
        return True
    else:
        return False


@auth.requires_login()
def project():
    '''Add new project'''
    name = request.vars.name
    prsup = request.vars.prsup
    prdir = request.vars.prdir
    prtd = request.vars.prtd
    prprod = request.vars.prprod
    res = request.vars.format
    fps= request.vars.fps
    mayafps= request.vars.mayafps
    #return prsup
    message = set()  # costum message for projectcreation page
    prs = db(db.project.name).select(orderby=db.project.modification_date)
    response.title = 'Create/Edit New Project'
    if (not name or not prsup or not prdir or not prtd or not prprod) and request.vars.create == 'true':
        #return prsup
        if not name:
            message.add('You must Enter a project name')
        if not prsup:
            message.add('You must select a supervisor for every project.')
        if not prdir:
            message.add('You must select a director for every project.')
        if not prtd:
            message.add('You must select a T.D. for every project.')
        if not prprod:
            message.add('You must select a producer for every project.')

    elif request.vars.create == 'true':
        supid = prsup.split()[3]
        dirid = prdir.split()[3]
        tdid = prtd.split()[3]
        prodid = prprod.split()[3]
        res = res.split('(')[1][:-1]
        fps = int(fps.split('(')[1][:-1])
        mayafps = int(mayafps.split('(')[1][:-1])
        supervisor = db(db.auth_user.id == supid).select().first()
        director = db(db.auth_user.id == dirid).select().first()
        td = db(db.auth_user.id == tdid).select().first()
        producer = db(db.auth_user.id == prodid).select().first()
        if not db(db.project.name == name).select().first():
            newpr = db.project.insert(name=name, supervisor=supervisor, \
                director=director, td=td, producer=producer, fps=fps, \
                mayafps=mayafps, size=res,owner=auth.user_id)
            newitem = db.item.insert(pid=newpr.uuid, type='project')
            group_id = 'pr-%s' % str(newpr.uuid)
            auth.add_group(group_id, 'Project: %s' % newpr.name)
            #for i in [supervisor, direcotr, producer, td]:
            auth.add_membership(group_id, supervisor.id)
            auth.add_membership(group_id, auth.user_id)
            auth.add_membership(group_id, director.id)
            auth.add_membership(group_id, td.id)
            auth.add_membership(group_id, producer.id)
            
            session.flash = 'Project created successfully.'
            redirect(URL(f='prview', vars={'pid': newpr.uuid}))

        else:
            message.add('Project name is not available.')

    return dict(message=message, prs=prs, is_master=check_permission())





@auth.requires_login()
def shot():
    '''Add new shots'''
    response.title = 'Create/Edit New shots'
    return dict()


@auth.requires_login()
def get_proj_seqs(pid):
    '''Get list of project sequences'''
    prdb = db(db.project.uuid == pid).select(db.project.id).first()
    seqs = db(db.sequence.project == prdb).select(orderby=db.sequence.number)

    return seqs


@auth.requires_login()
def get_seq_shots(sid):
    '''Get shots in a sequence'''
    seqdb = db(db.sequence.uuid == sid).select(db.sequence.id).first()
    seqShots = db(db.shot.sequence == seqdb).select(orderby=db.shot.number)
    return seqShots


@auth.requires_login()
def get_proj_shots(pid):
    '''Get shots of project'''
    seqs = get_proj_seqs(pid)
    shots = []
    for seq in seqs:
        seqShots = get_seq_shots(seq.uuid)
        for shot in seqShots:
            #print shot
            shots.append(shot)
    return shots


@auth.requires_login()
def get_shot_assets(shid):
    '''Get list of shot assets'''
    assets = set()
    shotdb = db(db.shot.uuid == shid).select(db.shot.assets).first()
    for asset in shotdb.assets:
        assets.add(asset)
    return assets


@auth.requires_login()
def get_seq_assets(sid):
    '''Get list of sequence assets'''
    assets = set()
    seqShots = get_seq_shots(sid)
    for shot in seqShots:
        for asset in get_shot_assets(shot.uuid):
            assets.add(asset)
    return assets


@auth.requires_login()
def get_proj_assets(pid):
    '''Get all assets of a project'''
    assets = set()
    seqs = get_proj_seqs(pid)
    for seq in seqs:
        for asset in get_seq_assets(seq.uuid):
            assets.add(asset)
    return assets


@auth.requires_login()
def prview():
    '''Project view'''
    pid = request.vars.pid
    if not pid:
        redirect(URL(f='project'))
    prdb = db(db.project.uuid == pid).select().first()
    if prdb and (auth.has_membership('pr-%s'%prdb.uuid, auth.user_id) or auth.has_membership('master', auth.user_id)):
        pass
    else:
        redirect(URL(c='home', f='index'))

    if prdb:
        response.title = 'Project: %s' % prdb.name.title()
        seq_list = get_proj_seqs(pid)
        
        if not prdb.qr:
            url = _getfull_host() + URL(c='home', f='prview', vars={'pid': prdb.uuid})
            qr = qrcode(url)
            if qr:
                prdb.update_record(qr=qr)
        if not prdb.chart1:
            chart1 = []
            for seq in seq_list:
                if seq.frames:
                    chart1.append(('S%s' % seq.number, seq.frames))
            if chart1:
                chart1file = piechart(chart1, \
                    title="%s Project Statistics - Sequence Duration" % prdb.name.title())
                prdb.update_record(chart1=chart1file)  # chart1 is about sequence involment

        shots = get_proj_shots(pid)
        frames = 0
        for i in shots:
            if i.frames:
                frames += i.frames
        assets = get_proj_assets(pid)
        progress = 12
        return dict(project=prdb, mode='pr', progress=progress, assets=assets, \
            shots=shots, frames=frames, seq_list=seq_list, is_master=check_permission())
    else:
        redirect(URL(f='project'))


@auth.requires_login()
def sqview():
    '''Sequence managing and viewing'''
    referer = request.env.http_referer
    sid = request.vars.sid
    pid = request.vars.pid
    if not sid:
        redirect(referer)
    sqdb = db(db.sequence.uuid == sid).select().first()
    if not sqdb.qr:
        url = _getfull_host() + URL(c='home', f='sqview', vars={'sid': sqdb.uuid})
        qr = qrcode(url)
        if qr:
            sqdb.update_record(qr=qr)

    if sqdb:
        response.title = 'Sequence %s - [%s]' % (sqdb.number, sqdb.project.name.title())
        shots = get_seq_shots(sid)
        if not sqdb.chart1:
            chart1 = []
            for shot in shots:
                if shot.frames:
                    chart1.append(('Shot%s' % shot.number, shot.frames))
            if chart1:
                chart1file = piechart(chart1, \
                    title="%s Project | Sequence%s Statistics - Shot Duration" % \
                        (sqdb.project.name.capitalize(), sqdb.number))
                sqdb.update_record(chart1=chart1file)  # chart1 is about sequence involment

        frames = 0
        for i in shots:
            if i.frames:
                frames += i.frames
        assets = get_seq_assets(sid)
        progress = 10
        data = response.render('home/prview.html', mode='seq', project=sqdb, \
        shots=shots, frames=frames, assets=assets, progress=progress, is_master=check_permission())

    return data


@auth.requires_login()
def shotview():
    '''View shot doc'''
    referer = request.env.http_referer
    shid = request.vars.shid
    if not shid:
        redirect(referer)
    shotdb = db(db.shot.uuid == shid).select().first()
    if not shotdb.qr:
        url = _getfull_host() + URL(c='home', f='shotview', vars={'shid': shotdb.uuid})
        qr = qrcode(url)
        if qr:
            shotdb.update_record(qr=qr)
    if shotdb:
        response.title = 'Shot %s - [Sequence %s] - [%s]' % (shotdb.number, shotdb.sequence.number, \
            shotdb.sequence.project.name.title())
        assets = get_shot_assets(shid)
        progress = 49
        frames = shotdb.frames
        data = response.render('home/prview.html', mode='shot', project=shotdb, \
        frames=frames, assets=assets, progress=progress, is_master=check_permission())
    return data


@auth.requires_login()
def asset():
    referer = request.env.http_referer
    asid = request.vars.asid
    if not asid:
        redirect(referer)  # TODO

    items = db(db.item.pid == asid).select().last()
    progress = 0
    response.title = 'Asset: %s' % items.uuid
    data = dict(item=items, is_master=check_permission(),\
        mode='asset')
    return data

#@auth.requires_membership(admin)


@auth.requires_login()
def delete_project():
    '''Ajax function'''
    pid = request.vars.pid
    pdb = db(db.project.uuid == pid)
    if len(pdb.select()):
        pdb.delete()
        session.flash = 'Project has been deleted!'
        return '''
            <script type="text/javascript">
            window.location='project';
            </script>
        '''


@auth.requires_login()
def delete_sequence():
    '''Ajax function'''
    sid = request.vars.sid
    sqdb = db(db.sequence.uuid == sid)
    pid = sqdb.select(db.sequence.project).first().project.uuid
    sq = sqdb.select().first()
    if sq:
        if sq.preview:
            sq.project.update_record(dirty=True)
            shots = db(db.shot.sequence == sq)
            shots.delete()
        sqdb.delete()
        session.flash = 'Sequence has been deleted!'
        return '''
            <script type="text/javascript">
            window.location='prview?pid=%s';
            </script>
        ''' % pid


@auth.requires_login()
def delete_shot():
    '''Ajax function'''


@auth.requires_login()
def delete_asset():
    '''Ajax function'''


@auth.requires_login()
def add_sequence(pid):
    '''Add sequence to the given project'''
    pdb = db(db.project.uuid == pid).select().first()
    if pdb:
        nseqs = db(db.sequence.project == pdb).count()
        newseq = db.sequence.insert(number=nseqs + 1, supervisor=pdb.supervisor, \
            project=pdb, uuid=uuid.uuid4())
        newitem = db.item.insert(pid=newseq.uuid, type='sequence')
    return newseq


@auth.requires_login()
def add_new_sequences():
    '''Add new sequences - Ajax base'''
    pid = request.vars.pid
    nons = request.vars.nons
    if pid and nons:
        try:
            nons = int(nons)
        except ValueError:
            return
        for i in range(nons):
            add_sequence(pid=pid)

        session.flash = '%d sequence(s) added succussfully.' % nons
        return '''
            <script type="text/javascript">
            window.location = "%s";
            </script>

        ''' % request.env.http_referer


@auth.requires_login()
def add_asset():
    '''Add sequence to the given project'''
    shid = request.vars.shid
    asname = request.vars.asname
    shdb = db(db.shot.uuid == shid).select().first()
    if shdb:
        #newas=1
        newas = db.asset.insert(shots=[shdb.id], name=asname, supervisor=shdb.supervisor, uuid=uuid.uuid4())
        oldassets = shdb.assets
        assets = oldassets + [newas]
        shdb.update_record(assets=assets)

    else:
        newas = db.asset.insert(name=asname, supervisor=auth.user_id, uuid=uuid.uuid4())
        newitem = db.item.insert(pid=newas.uuid, type='asset')
        session.flash = 'Asset ID:%s added succussfully.' % newas.id
        return '''
            <script type="text/javascript">
            window.location = "%s";
            </script>

        ''' % request.env.http_referer


@auth.requires_login()
def add_shot(sid):
    '''Add new shot to a sequence'''
    sqdb = db(db.sequence.uuid == sid).select().first()
    if sqdb:
        nshots = db(db.shot.sequence == sqdb).count()
        newshot = db.shot.insert(number=nshots + 1, supervisor=sqdb.supervisor, \
            sequence=sqdb, uuid=uuid.uuid4())
        newitem = db.item.insert(pid=newshot.uuid, type='shot')


@auth.requires_login()
def add_new_shots():
    '''Add new shots to sequence'''
    sid = request.vars.sid
    nons = request.vars.nons
    if sid and nons:
        try:
            nons = int(nons)
        except ValueError:
            return

        for i in range(nons):
            add_shot(sid=sid)

        session.flash = '%d shot(s) added succussfully.' % nons
        return '''
            <script type="text/javascript">
            window.location = "%s";
            </script>

        ''' % request.env.http_referer


@auth.requires_login()
def get_upload_folder():
    upload_folder = '%sstatic/uploads' % request.folder
    data = os.path.abspath(upload_folder)
    #print data
    return data


@auth.requires_login()
def get_path(fdb):
    '''generate file path based on given vfile db'''
    #fid = fdb.uuid
    #ext = fdb.ext
    upload_folder = get_upload_folder()
    dstpath = '%s/%s' % (upload_folder, fdb.name)
    data = os.path.abspath(dstpath)
    #print data
    return data


@auth.requires_login()
def process_videos():
    '''Process videos and generate previews'''


@auth.requires_login()
def upload():
    '''File uploader'''
    #print 'ok'
    #print request.vars.type
    upload_folder = '%sstatic/uploads' % request.folder
    referer = request.env.http_referer
    #print 'ok'
    utype = request.vars.type
    pid = request.vars.pid  # project
    sid = request.vars.sid  # sequence
    shid = request.vars.shid  # shot
    asid = request.vars.asid  # asset
    item = request.vars.item
    mitem = request.vars.mitem
    #itemuid = request.vars.item
    imgext = ['jpg', 'jpeg', 'tiff', 'tif', 'png', 'bmp']
    vidext = ['mpg', 'mp4', 'm4v', 'avi', 'flv', 'mov', '3gp', 'mkv']
    docext = ['pdf', 'txt', 'html']
    target = None
    #print 'hi'
    if 'file' in request.vars:
        #print 'request.vars.file'
        try:
            data = [(i.filename, i.file) for i in request.vars.file]
        except:
            data = [(request.vars.file.filename, request.vars.file.file)]

        for each in data: 
            fd = each[1]
            origname = each[0]
            #return origname
            ext = origname.split('.')[-1].lower()
            if utype == 'image' and not ext in imgext:
                session.flash = 'OoPssss!!! You need to select an image!'
                redirect(referer)
            if utype == 'video' and not ext in vidext:
                session.flash = 'OoPssss!!! You need to select a video file!'
                redirect(referer)
                #return ext, name


            #hashname = hashlib.sha256(data).hexdigest()

            #########  COPY FILE TO SERVER
            fid = uuid.uuid4()  # new file id
            #return fid
            #print fid
            newname = '%s.%s' % (fid, ext)
            #return newname
            dstpath = '%s/%s' % (upload_folder, newname)
            dst = open(dstpath, 'wb')  # open a new file
            shutil.copyfileobj(fd, dst)  # copy file
            #return dst
            dst.close()  # close it
            ######### CHECK FILE
            #return pid
            sha1 = sha1sum(dstpath)
            name = '%s/%s.%s' % (upload_folder, sha1, ext)
            if not os.path.isfile(name):
                os.rename(dstpath, name)  # rename file to it's hash

            else:
                os.remove(dstpath)

            oldfile = db(db.vfile.hash == sha1).select().first()
            #print oldfile
            if oldfile and os.path.isfile(get_path(oldfile)):
                #print 'old file is available'
                if not oldfile.process:
                    process = db.process.insert(isfinished=False)
                    oldfile.update_record(isvideo=True, process=process)
                if utype == 'video':
                    oldfile.process.update_record(isvideo=True, isfinished=False)  # send again for calculation

                newfile = oldfile

            else:
                if utype == 'video' and not item:
                    process = db.process.insert(name=os.path.basename(name))
                    newfile = db.vfile.insert(process=process, hash=sha1, \
                        rawname=origname, uuid=fid, ext=ext, \
                            name=os.path.basename(name), isvideo=True)
                else:  # it's thumbnal or attachment
                    newfile = db.vfile.insert(uuid=fid, ext=ext, hash=sha1, \
                        rawname=origname, name=os.path.basename(name))

                    


                newitem = db.item.insert(pid=newfile.uuid, type='vfile')

            if pid:
                target = db(db.project.uuid == pid).select().first()
            elif sid:
                target = db(db.sequence.uuid == sid).select().first()
                if target and utype == 'video':
                    target.update_record(dirty=True, ignore_shots=True)
                    target.project.update_record(dirty=True)
            elif shid:
                target = db(db.shot.uuid == shid).select().first()
                #print target.number
                if target and utype == 'video':
                    target.update_record(dirty=True)
                    target.sequence.update_record(dirty=True, ignore_shots=False)
                    target.sequence.project.update_record(dirty=True)
            elif asid:
                target = db(db.asset.uuid == asid).select().first()
            #return target
            if target and utype == 'image':
                target.update_record(thumb=newfile)
            elif target and utype == 'video':
                target.update_record(preview=newfile)
            
            #print request.vars.pid
            #print request.vars.pid
            if target and not item:
                ritem = db(db.item.pid == target.uuid).select().last()

            elif item:  #attachment
                ritem = db(db.item.pid == item).select().last()
                ### send a message
            #print item.uuid
            elif mitem:  # it is a message attachment
                ritem = db(db.item.uuid == mitem).select().last()

            if target:
                users=db(db.auth_user.id).select(db.auth_user.id, db.auth_user.last_name, db.auth_user.first_name)
                sender = db(db.auth_user.id==auth.user_id).select(db.auth_user.last_name).first()
                for user in users:
                    if user.id !=auth.user_id and auth.has_membership(auth.id_group('pr-%s' % target.uuid), user.id):
                        prot = '%s://%s' % (request.env.wsgi_url_scheme, request.env.http_host)
                        url = prot + URL(c='utils', f='vfile_comments', vars={'uuid':newfile.uuid})
                        descr = '%s added a newfile to review: %s' % (sender.last_name.title(), newfile.name)
                        subject = descr[:63]
                        message = '%s added a newfile to review: <br/><a href="%s">%s</a>' % \
                                (sender.last_name.title(), url, newfile.name)
                        newm = db.message.insert(uuid=uuid.uuid4(), \
                            sender=auth.user_id, target=user.id, body=message, descr=descr, subject=subject)
                #print ritem
            if (mitem or item) and ritem.vfiles and newfile.id not in ritem.vfiles:
                ritem.update_record(vfiles=[newfile.id] + ritem.vfiles)
            elif (mitem or item) and not ritem.vfiles:
                ritem.update_record(vfiles=[newfile.id])

            if not oldfile:
                session.flash = '%s uploaded to database.' % utype.title()
            else:
                session.flash = '%s was available and linked to this item.' %\
                    utype.title()
            #if utype != 'video':
        redirect(referer)
            #else:
               # process_videos()





@auth.requires_login()
def changesup():
    '''change supervisor'''
    sid = request.vars.sid
    #return sid
    shid = request.vars.shid
    pid = request.vars.pid
    sup = request.vars.sup
    tdb = None
    #return sup, shid, sid
    if pid:
        tdb = db(db.project.uuid == pid).select().first()
    if sid:
        tdb = db(db.sequence.uuid == sid).select().first()
    elif shid:
        tdb = db(db.shot.uuid == shid).select().first()
    if sup:
        supid = sup.split()[3]
        if supid:
            supid = int(supid)
    if tdb:
        tdb.update_record(supervisor=supid)
        response.flash = 'Changed!'
        return '''
            <script type="text/javascript">
            window.location = "%s";
            </script>

        ''' % request.env.http_referer

    else:
        return sid, shid


@auth.requires_login()
def changeDNotes():
    '''Change direcotr notes'''
    seq = request.vars.seq
    pr = request.vars.pr
    shot = request.vars.shot
    note = request.vars.note
    tdb = None
    if note:
        if pr:
            tdb = db(db.project.uuid == pr).select().first()
        if seq:
            tdb = db(db.sequence.uuid == seq).select().first()
        if shot:
            tdb = db(db.shot.uuid == shot).select().first()
    if tdb:
        tdb.update_record(description=XML(note, sanitize=True))

        return note
    else:
        return uid


@auth.requires_login()
def video_process():
    return 'ok'

@auth.requires_login()
def video():
    '''show it'''
    vname = request.vars.vname
    fdb = db(db.vfile.name == vname).select().first()
    projects = db(db.project.preview == fdb).select()
    seqs = db(db.sequence.preview == fdb).select()
    shots = db(db.shot.preview == fdb).select(db.shot.sequence, db.shot.id, db.shot.uuid, db.shot.number, db.shot.previews)
    target = projects or seqs or shots
    if vname:
        return dict(vname=vname, fdb=fdb, shots=shots, seqs=seqs, projects=projects, target=target)


@auth.requires_login()
def download():
    '''Download vfile'''
    fid = request.vars.fid
    ext = request.vars.ext
    dl = request.vars.dl
    #return dl
    if not ext:
        ext = 'preview'
    #fname = request.vars.fname
    upf = '%sstatic/uploads' % request.folder
    if fid:
        fdb = db(db.vfile.uuid == fid).select().first()

    if fdb:
        path = '%s/%s' % (upf, fdb.name)
        f = cStringIO.StringIO()
        if os.path.isfile(path):
            data = open(path, 'rb').read()
            response.headers['Content-Type'] = gluon.contenttype.contenttype('.' + fdb.name)

            if dl or ext not in ['jpg', 'png', 'tiff', 'pdf', 'html']:

                response.headers['Content-Disposition'] = "attachment; filename=%s" % \
                    (fdb.rawname or fdb.name)
            return data
        else:
            session.flash = 'File is not available for download!'
            redirect(request.env.http_referer)


def attachments():
    '''ajax loading'''
    ipid = request.vars.ipid
    mode = request.vars.mode
    if ipid:
        item = db(db.item.pid == ipid).select().last()
        
        if item:
            return dict(item=item, prid=ipid, mode=mode, is_master=check_permission())


@auth.requires_login()
def assets():
    '''List all of assets'''
    response.title = 'Assets'
    assets = db(db.asset.id > 0).select()
    return dict(assets=assets)


def help():
    '''help center'''
    response.title = 'Help Center'
    docsdir = '%s/Docs' % request.folder
    pure_tut_list = os.listdir(docsdir)
    tut_list = [os.path.basename(i).split('.')[0].split('-')[1] for i in pure_tut_list if not '~' in i]
    #return tut_list
    topicname = request.vars.topic
    topic = None
    if topicname:
        topicfile = None
        for name in pure_tut_list:
            if topicname in name:
                topicfile = name
        if topicfile:
            topic = open('%s/%s' % (docsdir, topicfile), 'r').read()
    return dict(tut_list=tut_list, topic=XML(topic))


def changeSupUi():
    return dict()


def prsettings():
    '''Project settings lightbox'''
    pid = request.vars.pid
    project = db(db.project.uuid == pid).select().first()
    users = db(db.auth_user).select()
    return dict(project=project, users=users)

def make_caption():
    text = request.vars.text
    data = '''
    WEBVTT

00:00.700 --> 00:02.110
Welcome to VixenServer!

00:04.500 --> 00:05.000
[ Splash!!! ]

00:05.100 --> 00:06.000
[ Sploosh!!! ]
    '''
    return data
    
def remove_preview():
    '''remove seq or shot preview'''
    shotid = request.vars.shotid
    sid = request.vars.sid
    referer = request.env.http_referer

    if shotid:
        shot = db(db.shot.uuid == shotid).select(db.shot.preview, db.shot.thumb, db.shot.id, db.shot.frames).first()
        shot.update_record(preview=None, thumb=None, frames=0)
        #return shot.number
    elif sid:
        seq = db(db.sequence.uuid == sid).select(db.sequence.preview, db.sequence.thumb, db.sequence.id, db.sequence.frames).first()
        seq.update_record(preview=None, thumb=None, frames=0, dirty=True)
    return '''
        <script>
            window.location="%s";
        </script>
    ''' % referer
        
