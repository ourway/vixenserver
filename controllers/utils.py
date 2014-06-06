from datetime import datetime as dt
import urllib2
import time
import uuid
import os
import sys
import re
import socket
import docx
import string
import shutil
import datetime
import getpass
import threading
from subprocess import Popen, PIPE, call  # everything nedded to handle external commands


###============GIT TOOLS====================


class Process(threading.Thread):
    '''Run ftp server'''
    def __init__(self, execfn):
        threading.Thread.__init__(self)
        self.execfn = execfn

    def run(self):
        '''General external process'''
        p = Popen(self.execfn, shell=True, env=os.environ,
                  stdout=PIPE, universal_newlines=True)  # process
        (stdout, stderr) = p.communicate()
        #print execfn
        #p.wait()
        return (stdout, stderr)


def execute(cmd):
    '''execute a command in threading mode'''
    pr = Process(cmd)
    data = pr.start()
    return data

def runGitCmd(prdb, args):
    '''Run a git command for a project'''
    prpath = prdb.path
    gitdir = '%sGIT/%s' % (request.folder, prdb.name)
    if not os.path.isdir(gitdir):
        os.makedirs(gitdir)
    execfn = ' '.join(['git --git-dir="%s" --work-tree="%s"' %
        (gitdir, prpath)] + list(args))
    #print execfn
    return execute(execfn)


def gitadd(prdb, filelist):
    flist = '"%s"' % '" "'.join(filelist)
    args = ['add', flist]  # generate argument
    data = runGitCmd(prdb, args)
    return data


def _getfull_host():
    result = '%s://%s' % (request.env.wsgi_url_scheme, request.env.http_host)
    return result


def comment_core():
    item = db(db.item.pid == request.vars.item).select().first()
    if not item:
        item = db.item.insert(pid=request.vars.item)

    old_comments = db(
        db.comment.item == item.id).select()  # list of comments db
    return dict(item=item, old_comments=old_comments, likes=item.likes)


def commenter():
    body = None
    actor = None  # commenter writer
    author = request.vars.author  # post auther
    asc = string.ascii_lowercase
    for i in request.vars.keys():
        if 'comment_body' in i:
            body = request.vars[i]
        if 'actor' in i:
            actor = request.vars[i]
    #print 'oh, i lunched'
    '''global commenting controller'''
    #print body
    pid = request.vars.pid
    comment_id = request.vars.com_id
    item = request.vars.item
    c_item = request.vars._citem  # for deletation usage
    if body and actor == str(auth.user_id):
        body = str(XML(body.replace('\n', ' '), sanitize=True))
        new_comment = db.comment.insert(body=body, item=item, actor=actor)
        userdb = auth.user
        #print ownerdb.name, userdb.name
        num_of_comments = db(db.comment.item == item).count()
        clean_name = '%s %s' % (
            userdb.first_name.title(), userdb.last_name.title())
        #print post_url

        return '''
                <script type="text/javascript">
                    var pid = '%s';
                    primage = '%s';
                    var num = %s;
                    var cmid = '%s';
                    $('#comments_show_div_' + pid).append(' <div id="c%s" class=comment_section><span class="com_body" style="color:#3B5998;cursor:pointer" title="%s"><a><b style="margin-left:-5px;">%s</b></a></span>&nbsp;<div id="tmp_div_'+cmid+'" style="white-space:normal;width:345px;"></div><br/><div style="display:inline-block;margin-top:8px;"><span title="%s" style="font-size:11px;color:#919191;margin-left:1px;">%s</span> . <a style="display:none;" class="like_but like_series"></a> <span class="num_of_cm_likes" style="display:none;color:#6d84b4;margin-right:5px;margin-left:-2px;">0</span><a class=like_cm_' + pid + '>Like</a> .  <a class=remove_cm_' + pid + '>Remove</a></div></div>');
                    //cleaning textarea
                    $('#comment_body_' + pid).val('');
                    $('#comment_body_' + pid).css('height','16px');
                    $('.cm_numofolds_' + pid).html(num);
                    $('.cm_numofolds_' + pid).fadeIn();
                    $('#cm_comment_icon_' + pid).fadeIn();
                    $('#tmp_div_' + cmid).html(html_sanitize("%s"));
                    $('.cm_submit_' + pid).html('Post');
                </script>

               ''' % (pid, URL(c='static', f='images/profile_temple_photo_tiny.gif'),
                num_of_comments, new_comment, new_comment, clean_name,
                    clean_name, dt.ctime(new_comment.creation_date),
                        prettydate(new_comment.creation_date, T), body.replace('\r', ' ').replace('\n', ' ').replace('\r\n', ' '))
    elif request.args and request.args[-1] == 'delete' and comment_id and c_item:
        comment_id = int(comment_id[1:])  # get the deleted comment id
        item_id = db(db.comment.id == int(comment_id)).select().first().item
        pid = db(db.item.id == item_id).select().first().pid
        db(db.comment.id == comment_id).delete()
        #print pid, item
        num_of_comments = db(db.comment.item == int(
            c_item)).count()  # num of comments after delete
        #print num_of_comments
        #now reload the comment area...
        return '''
                <script type="text/javascript">
                    var com_count = %s;
                    var pid = '%s';
                    $('.cm_numofolds_' + pid).html(com_count);
                    if (com_count == 0){
                        $('.cm_numofolds_' + pid).fadeOut();
                        $('#cm_comment_icon_' + pid).fadeOut();
                    }
                </script>
               ''' % (num_of_comments, pid)


def liker():
    '''Like buttom functionality'''
    if request.args:
        userdb = auth.user
        if request.args[-1] == 'comment':
            comment_id = request.vars.com_id
            pid = request.vars._pid
            #infodb     = db(db.item.pid == pid).select().first()
            commentdb = db(
                db.comment.id == int(comment_id[1:])).select().first()
            #ownerdb    = db(db.user.id == infodb.owner).select().first()
            #print ownerdb.name
            if not commentdb:
                return 'Comment deleted or not available'
            else:
                cdb = commentdb

                clikes = cdb.likes
                #print clikes
                # end if

                if not userdb.id in clikes:
                    clikes.insert(0, userdb.id)
                    cdb.update_record(likes=clikes)
                    #new_event = db.event.insert(action='liked', item=new_item)
                else:
                    clikes.remove(userdb.id)
                    cdb.update_record(likes=clikes)
                #print clikes
                comment_get_Url = URL(r=request, c='utils',
                                      f='comment_core', vars={'item': pid})

                return '''
                        <script type="text/javascript">
                            var cmid   = '%s';
                            var pid    = '%s';
                            var likes  = %s;
                            $('#' + cmid + ' span.num_of_cm_likes').html(likes);
                                if (likes>0){
                                    $('#' + cmid +  ' a.like_but').fadeIn();
                                    $('#' + cmid + ' span.num_of_cm_likes').fadeIn();
                                }
                                else{
                                    $('#' + cmid +  ' a.like_but').fadeOut();
                                    $('#' + cmid + ' span.num_of_cm_likes').fadeOut();
                                }
                        </script>
                       ''' % (comment_id, pid, len(clikes))

                #
        if request.args[-1] == 'page':
            page_pid = request.vars.page_id
            infodb = db(db.item.pid == page_pid).select().first()
            user_full = '%s %s' % (
                userdb.first_name.title(), userdb.last_name.title())
            ownerdb = db(db.auth_user.id == infodb.owner).select().first()
            #print ownerdb.email
            if not infodb:
                return
            else:
                pdb = infodb
                userdb = auth.user
                plikes = pdb.likes
                page_address = request.env.http_referer

                if not userdb.id in plikes:
                    plikes.insert(0, userdb.id)
                    #print plikes
                    pdb.update_record(likes=plikes)

                    ##==========================================================
                else:  # if user clicks on unlike button:
                    plikes.remove(userdb.id)
                    #print plikes
                    pdb.update_record(likes=plikes)
                return '''
            <script type="text/javascript">
                var pid = '%s';
                var ltext = $('.plikebut').html();
                var plikes = %s;
                $('#cm_numoflikes_' + pid).html(plikes);
                if (plikes == 0){
                    $('#likenumiconshow_' + pid).fadeOut(); //hide icon
                    $('#cm_numoflikes_' + pid).fadeOut(); //hide number
                    }
                else{
                    $('#likenumiconshow_' + pid).fadeIn(); //hide icon
                    $('#cm_numoflikes_' + pid).fadeIn(); //hide number
                }                         
            </script>                        
            ''' % (page_pid, len(plikes))
    return redirect(request.env.http_referer)


def mail_box():
    targetId = request.vars.target
    target = db(db.auth_user.id == targetId).select().first()
    item = db.item.insert(uuid=uuid.uuid4())
    return dict(target=target, item=item)


def mailer_ajax():
    '''Ajax tool for adding messages to mail queue'''
    targetId = request.vars.tid  # target id
    message = request.vars.message
    itemuuid = request.vars.item
    mtype = request.vars.mtype  # type of message, for eample it's blog suggesion or post
    #print itemid,targetId,message,auth.user_id
    if itemuuid and targetId and message and auth.user_id:
        #return 'ok'
        target = db(db.auth_user.id == targetId).select().first()
        email = target.email
        item = db(db.item.uuid == itemuuid).select().last()
        #return item.id
        message = message.replace('\n', '<br/>') + '<br/>'
        sender = '%s %s' % (
            auth.user.first_name.title(), auth.user.last_name.title())
        mbody = 'Hi %s, %s wrote you a message:<br/> <p style="color:#07004D;margin-top:10px;">%s</p>' % (target.first_name.title(), sender, message)
        #return len(item)
        #return mbody
        subject = 'New message from %s' % (sender)

        newm = db.message.insert(uuid=uuid.uuid4(), \
                sender=auth.user_id, target=target, body=message)

        #print newm
        #return newm.uuid
        item.update_record(pid=newm.uuid)
        

        newmail = db.mail_queue.insert(message=newm, priority=4, mtype=request.vars.mtype, mbody=mbody, email=email, subject=subject)  # Add mail to queue  # =======
        #return newmail.id
        return '''
            <script>
                $('#mbcontents').fadeOut();
                setTimeout("$('#whole_box').fadeOut(500);",2800);
                $('#attachform').submit();
                setTimeout("$('#whole_box').trigger('close');",3500);
                setTimeout("$('#whole_box').remove();",3600);

            </script>
            <p style="font-size:10px;vertical-align:center" align="center"><b>Message Sent!</b><br/>
            </p>
        '''
    else:  # Inputs are not complete
        return '''
                <script type="text/javascript">
                    $('#mailbox_sender').html('Send');
                </script>
                <p align="center" style="color:darkred"><b>Error!</b> Please check again.</p>
        '''


def gettime():
    tt = time.ctime()
    return ''.join(tt.split()[:3]) + ' - ' + ':'.join(tt.split()[3].split(':')[:2])


def get_number_of_messages():
    '''Ajax call'''
    mdb = db((db.message.target == auth.user_id) & (
        db.message.unread == True)).select()
    if mdb:
        data = '''
        <li><a id="mcount" href="%s" style="background:#fff;color:#fff"><b class="notification">%s</b></a></li>
        <script type="text/javascript">
            $('#eicon').html('%s');
            var isaudio = $('audio').length;
            if (%s<%s){
            $('body').append('<audio src="%s" autoplay="true" ></audio');
            $.titleAlert("* New Mail! *", {
                //requireBlur:true,
                stopOnFocus:true,
                interval:500
            });

            }
        </script>

        ''' % (URL(c='utils', f='messages', args='inbox', vars={'filter': 'unread'}),
            len(mdb), len(mdb), session.messages, len(mdb), URL(c="static", f="sound/gotmail.wav"))

        session.messages = len(mdb)
        return data
    else:
        return ''


@auth.requires_login()
def messages():
    '''Messages area'''
    nm = len(db((db.message.target == auth.user_id) & (
        db.message.unread == True)).select())
    if nm:
        response.title = "Messages (%s)" % nm
    else:
        response.title = 'Messages'
    #messages = db(db.message.target==auth.user_id).select()
    return dict()


def inbox():
    '''ajax call'''
    messages = db(db.message.target == auth.user_id).select(
        orderby=~db.message.creation_date)
    #for i in messages: print i.target
    data = response.render('utils/inbox.html', messages=messages, mode='inbox')
    return data


def sent_items():
    '''ajax call'''
    messages = db(db.message.sender == auth.user_id).select(
        orderby=~db.message.creation_date)
    data = response.render('utils/inbox.html', messages=messages, mode='sent')
    return data


def showm():
    '''Show mwssage, ajax call'''
    mid = request.vars.mid
    message = db(db.message.uuid == mid).select().first()
    #print message.target.email
    #print message.target
    if message:
        #print message.target
        if auth.user_id == message.target and message.unread:  # if target reads it for first time:
            #print 'ok'
            message.update_record(unread=False, read_date=dt.now())
            if session.messages and session.messages > 0:
                session.messages = session.messages - 1
            #db.commit()
            #print message.unread
        return dict(message=message)
    else:
        return 'Message is not in database!'


def crew():
    '''Show members list with ability to send messages'''
    crewdb = db(db.auth_user.id).select(orderby=db.auth_user.first_name)

    response.title = 'Crew - Find members here'
    return dict(crewdb=crewdb)


def gen_message_for_shot(shot, key, target, action):
            #print key
            section = key.split('_')[0]
            shoturl = '%s%s' % (_getfull_host(
                ), URL(c='home', f='shotview', vars={'shid': shot.uuid}))
            #print shoturl
            sequrl = URL(
                c='home', f='sqview', vars={'sid': shot.sequence.uuid})
            prurl = URL(c='home', f='prview', vars={'pid':
                        shot.sequence.project.uuid})
            subject = '%s of Shot%s/Seq%s of %s project is %s' % (section.title(),
                shot.number, shot.sequence.number, shot.sequence.project.name.split()[0].capitalize()[:10], action[:10])
            if target == 'director':
                target = shot.sequence.project.director
            elif target == 'supervisor':
                target = shot.supervisor
            elif target == 'responsible':
                target = eval('shot.%s_sup' % section)
                #print target.email
            message = '''
            Dear %s, %s of <a href="%s"><b>Shot%s</b></a> - <b>Sequence%s</b> of <b>%s</b> project is %s.
            ''' \
                % (
                    target.first_name.title(), section, shoturl, shot.number, shot.sequence.number,
                   shot.sequence.project.name.capitalize(), action)

            descr = '%s_%s_%s' % (key, shot.uuid, target.id)
            #print descr
            oldm = db(db.message.descr == descr).select().last()
            if oldm:
                print 'There is an old item: %s' % oldm.uuid
            if target.id != auth.user_id:
                if not oldm:
                #print target.email
                    newm = db.message.insert(
                        uuid=uuid.uuid4(), subject=subject, sender=auth.user_id,
                        descr=descr, target=target, body=message)

                    db.mail_queue.insert(priority=4, mtype='message', mbody=message, email=target.email, subject=subject)  # Add mail to queue  # =======


def update_shot():
    shot = db(db.shot.uuid == request.vars.shid).select().first()
    vars = request.vars
    ml = dict()
    for i in vars:
        ml[i.lower()] = vars[i]

    for key in ml.keys():
        if '_iswip' in key:
            if not eval('shot.%s' % key):
                cmd = 'shot.update_record(%s=True, %s_date=dt.now())' % (
                    key, key)
                eval(cmd)

    for key in ml.keys():
        if '_iscompleted' in key:
            if not eval('shot.%s' % key):
                cmd = 'shot.update_record(%s=True, %s_date=dt.now())' % (
                    key, key)
                eval(cmd)
                gen_message_for_shot(shot, key, target='director', action='completed. Please review the item')

    for key in ml.keys():
        if '_isconfirmed' in key:
            if not eval('shot.%s' % key):
                cmd = 'shot.update_record(%s=True, %s_date=dt.now())' % (
                    key, key)
                eval(cmd)
                gen_message_for_shot(shot, key, target='supervisor',
                                     action='confirmed by director')
                gen_message_for_shot(shot, key, target='responsible', action='confirmed by director. Great job! Thank you')

    for key in ml.keys():
        if '_complexity' in key:
            value = ml[key].split()[1][1]
            cmd = 'shot.update_record(%s=%s)' % (key, value)
            eval(cmd)

    for key in ml.keys():
        if 'characters' in key:
            try:
                value = int(ml[key])
                cmd = 'shot.update_record(%s=%s)' % (key, value)
                eval(cmd)
            except ValueError:
                session.flash = 'Enter a number for characters.'

    for key in ml.keys():
        if '_sup' in key:
            sup = ml[key]
            if sup:  # if it's not empty:
                supid = sup.split()[3]
                supdb = db(db.auth_user.id == supid).select().first()
                cmd = 'shot.update_record(%s=%s)' % (key, supdb.id)
                gen_message_for_shot(shot, key, target=supdb, action='is your new task to do. Good Luck!')
            else:
                cmd = 'shot.update_record(%s=None)' % (key)
            eval(cmd)

    redirect(request.env.http_referer)


def readdocx():
    '''Microsoft document reader'''
    did = request.vars.did
    highlight = request.vars.h
    if not highlight:
        highlight="VixenServer"
    fdb = db(db.vfile.uuid == did).select().last()
    upfolder = '%sstatic/uploads' % request.folder
    frpath = '%s/%s' % (upfolder, fdb.name)
    fpath = os.path.abspath(frpath)
    if fdb and fdb.ext == 'txt':
        if os.path.isfile(fpath):
            data = open(fpath, 'r').read()
            data = '<p style="padding:5px;">{}<p'.format(data)
            return data
    if fdb and fdb.ext == 'docx':
        if os.path.isfile(fpath):
            document = docx.opendocx(fpath)
            paratextlist = docx.getdocumenttext(document)
            newparatextlist = []
            for paratext in paratextlist:
                newparatextlist.append(paratext.encode("utf-8"))

            asc = string.ascii_lowercase
            lang = 'en'
            #print newparatextlist[0][0]
            if newparatextlist and not newparatextlist[0][0].lower() in asc:
                lang = 'fa'
            data = '<br/>'.join(newparatextlist).replace(highlight, '<b style="background:yellow;color:darkgreen">{}</b>'.format(highlight))
            data = '<div style="padding:5px;">{}</div>'.format(data)
            response.title = 'Document: %s' % fdb.rawname
            if not request.vars.raw == 'true':
                return dict(name=fdb.rawname, data=XML(data), lang=lang)
            else:
                if lang=='fa':
                    style="padding:2px;background:#fff;direction:rtl;font-family:terafik;font-size:10px;"
                else:
                    style="padding:2px;background:#fff;font-family:terafik;font-size:10px;"
                return '<div style="%s">%s</div>' % (style, XML(data))

    else:
        session.flash = 'Error reading document!'
        redirect(request.env.http_referer)


def is_master():
    '''get the level of permission for a user'''
    gr = db(db.auth_membership.user_id == auth.user_id).select().first()
    if gr and gr.group_id == 1:
        return True
    else:
        return False


def shot_details():
    '''Ajax base load of shot details'''
    shid = request.vars.shid
    shot = db(db.shot.uuid == shid).select().first()
    if shot:
        return dict(shot=shot, is_master=is_master())


def shot_stats():
    '''Ajax base load of shot statistics'''
    shid = request.vars.shid
    shot = db(db.shot.uuid == shid).select().first()
    if shot:
        tasks = ['animatic', 'animation', 'layout', 'lighting',
            'preview', 'compositing', 'rendering']
        xtimelist = []
        ytimelist = []
        for task in tasks:
            wid = eval('shot.%s_iswip_date' % task)
            cd = eval('shot.%s_iscompleted_date' % task)

            if wid and not cd:
                dow = round(
                    (now - wid).days + (now - wid).seconds / 86400.0, 3)
            elif wid and cd:
                dow = round((cd - wid).days + (cd - wid).seconds / 86400.0, 3)
            else:
                dow = 0
            pass

            if dow:
                ytimelist.append(str(dow))
                xtimelist.append('"%s"' % task.title())
            xt = ','.join(xtimelist)
            yt = ','.join(ytimelist)
        print xt, yt
        return dict(
            xt=xt, yt=yt, label='Shot%s Timing Statisctics' % shot.number, cr='days',
            fill='#43B5DE', stroke='#37A1B5')


def crew_activity():
    '''ajax statistics'''
    crew = db(db.auth_user.id > 0).select()
    xtimelist = []
    ytimelist = []
    for i in crew:
        leadshots = db(db.shot.supervisor == i).select()
        if len(leadshots):
            ytimelist.append(str(len(leadshots)))
            xtimelist.append(
                "'%s %s'" % (i.first_name.title(), i.last_name.title()))
    xt = ','.join(xtimelist)
    yt = ','.join(ytimelist)

    data = response.render('utils/shot_stats.html', xt=xt, yt=yt,
            label='Crew Supervising Statisctics - Shot Base', cr='Shots',
            fill='#37B57A', stroke='#37A1B5')
    return data


def search_message():
    '''Ajax base search messages'''
    query = request.vars.query
    querydb = db.message.body.contains(
        query) & (db.message.target == auth.user_id)
    messages = db(querydb).select(orderby=~db.message.creation_date)[:12]
    data = response.render(
        'utils/inbox.html', messages=messages, mode='search')
    return data


def make_read():
    '''Ajax base make all messages read'''
    query = db.message.target == auth.user_id
    db(query).update(unread=False)
    session.messages = 0
    return '''<script>$('#eicon').html('0');</script>'''

def convert_tools(item):
    #print 'got item'
    item = db(db.item.pid==request.vars.item).select(db.item.vfiles).last()
    if item:
        #print 'Item not found!'
        for each in item.vfiles:
            target = db(db.vfile.id==each).select(db.vfile.ext, db.vfile.id, db.vfile.name).last()
            formats=['psd','tif', 'jpg', 'bmp', 'png', 'pdf', 'svg']
            if target and target.ext in formats:
                imgpath = '%s/static/uploads/%s' % (request.folder, target.name)
                path=os.path.realpath(imgpath)
                #print path
                if target.ext in ['psd','tif', 'pdf']:
                    cmd = 'convert "%s[0]" "%s.png"' % (path,path)
                    if not os.path.isfile('%s.png' % path):
                        os.system(cmd)
                        #print '%s converted.' % path
                    path = '%s.png' % os.path.realpath(imgpath)
                cmd2 = 'convert "%s[0]" -scale 220 "%s.thumb.png"' % (path,path)
                if not os.path.isfile('%s.thumb.png' % path):
                    os.system(cmd2)

def ajax_convert_tools():
    if request.vars.item:
        convert_tools(request.vars.item)
    return ''

def img_viewer():
    '''Image viewer based on a file uuid'''
    item = None
    if request.vars.item:
        
        convert_tools(item)                    
    #fid = request.vars.fid
    #print fid
    #fdb = db(db.vfile.id==int(fid)).select().first()
        return dict(pid=request.vars.item)


def report():
    '''Crew reports to admin'''
    response.title = 'My Reports'
    user_reports = db(
        db.report.creator == auth.user_id).select(db.report.created)
    today_reports = []
    today = str(datetime.datetime.now()).split()[0]
    for rep in user_reports:
        crdate = str(rep.created).split()[0]
        if crdate == today:
            today_reports.append(rep)

    repno = len(today_reports) + 1
    return dict(today=today, repno=repno)


def savereport():
    '''ajax function'''
    report = request.vars.body
    if report:
        db.report.insert(body=report)
        session.flash = "Thank you, your report has been sent to your supervisor."
    else:
        session.flash = "Please write your report before sending!"
    return '''
        <script type="text/javascript">
            var newloc="%s";
            window.location = newloc;
        </script>
        ''' % (request.env.http_referer)


def story():
    '''story line base of a project'''
    pid = request.vars.pid
    pdb = db(db.project.uuid == pid).select().first()
    seqs = db(db.sequence.project == pdb).select(orderby=db.sequence.number)
    response.title = 'The story of %s' % pdb.name.title()

    return dict(pdb=pdb, seqs=seqs)


def sendMC(command, devmode=True):
    '''Send a command to maya'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 29999
    try:
        sock.connect(("%s" % '192.168.2.102', port))
        sock.send(command)
        sock.shutdown(2)
        sock.close()
        return True
    except Exception, e:
        print e
        return


def getServerIp():
    return request.env.http_host.split(':')[0]


def getBasicCommands():
    data = '''
import maya.cmds as mc
from pymel.core import *
from vixen.utils import worker
reload(worker)
Worker = worker.Worker
Worker(server_ip='%s', dbname='vixenserver', dbusr='vishka', dbpwd='rrferl')
''' % getServerIp()
    return data


def maya_run_command():
    '''run a python command inside maya'''
    command = request.vars.command
    data = '''
import maya.cmds as mc
from pymel.core import *
%s
''' % command

    sendMC(data)
    return '<script></script>'


def maya():
    ''' Maya assets control center. main connection to Vixen for Maya'''
    response.title = XML('your Maya&reg;')

    command = getBasicCommands()
    command += 'warning("Vixen Server now connected to your workspace.")'
    data = sendMC(command)
    return dict(message=data)


def checkdir():
    '''ajax base check directory'''
    mayapath = request.vars.mayapath
    if os.path.isdir(mayapath):
        return '<span style="color:darkgreen">ok</span>'
    else:
        return '<span style="color:darkred">Error!</span>'


def runGitBasic(prdb):

    runGitCmd(prdb, ['init'])  # init project
    runGitCmd(prdb, ['commit -am "restruct"'])  # init project


def mayastruct(prdb):
    '''Create a structure of project for Maya base products'''
    prpath = prdb.path
    runGitBasic(prdb)
    tmp_folder = "%stemplates" % request.folder
    scenes_path = '%s/scenes' % prpath
    images_path = '%s/sourceimages' % prpath
    renders_path = '%s/renders' % prpath
    refs_path = '%s/refs' % prpath
    data_path = '%s/data' % prpath
    track_files = set()
    seqs = db(db.sequence.project == prdb).select(orderby=db.sequence.number)
    #print seqs
    for i in [scenes_path, images_path, renders_path, refs_path, data_path]:
        if not os.path.isdir(i):
            os.makedirs(i)
        for seq in seqs:
            #print seq
            seq_path = '%s/seq%s' % (i, seq.number)
            seqShots = db(
                db.shot.sequence == seq).select(orderby=db.shot.number)
            #print seq_path
            if not os.path.isdir(seq_path):
                os.makedirs(seq_path)

            for sp in seqShots:
                shotpath = '%s/shot%s' % (seq_path, sp.number)
                if not os.path.isdir(shotpath):
                    os.makedirs(shotpath)
                tmpfilename = 's_%s_%s.mb' % (prdb.size, prdb.fps)
                mayatmplate = '%s/maya_files/%s' % (tmp_folder, tmpfilename)
                #print mayatmplate

                if i == scenes_path and os.path.isfile(mayatmplate):
                    target = '%s/%s_seq%s_shot%s.mb' % (shotpath, prdb.name[:4],
                    sp.sequence.number, sp.number)
                    track_files.add(target)  # add to git tracked list

                    if not os.path.isfile(target):
                        shutil.copyfile(mayatmplate, target)
                                        #copy a maya template scene file

    gwstmp = '%s/maya_workspace/workspace.mel' % tmp_folder
    gwsfile = '%s/workspace.mel' % prpath
    track_files.add(gwsfile)
    shutil.copyfile(gwstmp, gwsfile)
    shutil.copyfile('%s/gitignore/global_gitignore' % tmp_folder,
                    '%s/.gitignore' % prpath)
    #shutil.copyfile('%s/gitignore/maya_files_gitignore' % tmp_folder, '%s/.gitignore' % scenes_path)
    #shutil.copyfile('%s/gitignore/sourceimages_gitignore' % tmp_folder, '%s/.gitignore' % images_path)

    gitadd(prdb, track_files)  # run git add command


    #execute('gedit')
    #pr = Process('gedit')
    #pr.start()


def saveprsettings():
    pid = request.vars.pid
    mayapath = request.vars.mayapath
    software_3d = request.vars.software_3d.split()[0]
    software_comp = request.vars.software_comp.split()[0]
    project = db(db.project.uuid == pid).select().first()
    if os.path.isdir(mayapath):
        project.update_record(path=mayapath, software_3d=software_3d,
            software_comp=software_comp)
        return '<span style="color:darkgreen">Changed successfully</span>'


def struct():
    '''Struct Project folders'''
    pid = request.vars.pid
    project = db(db.project.uuid == pid).select().first()
    if project.software_3d == 'maya':
        mayastruct(project)


def rendersheet():
        '''Project render sheet'''
        response.title = 'Render Sheet'
        pid = request.vars.pid
        prdb = db(db.project.uuid == pid).select().first()
        seqs = db(
            db.sequence.project == prdb).select(orderby=db.sequence.number)
        return dict(seqs=seqs, prdb=prdb)


def update_rendersheet():
        '''Ajax based function'''
        suuid = request.vars.sequuid
        sdb = db(db.sequence.uuid == suuid).select().first()
        shots = db(db.shot.sequence == sdb).select()
        # keys that we need to update in database each time
        keys = ['startrange', 'endrange', 'preview_iscompleted', 'compositing_iscompleted',
            'rendering_iscompleted', 'fixed_cam', 'rendering_isconfirmed', 'rendering_desc']
        for shot in shots:
            # generate a string
            #  shot.update_record(a=x, b=y)
            valdict = {}
            for key in keys:
                keyval = eval('request.vars.shot_%s_%s' % (shot.id, key))

                if keyval == 'on':
                    valdict[key] = True
                elif keyval == 'none' or keyval == 'None':
                    valdict[key] = False
                else:
                    valdict[key] = keyval

            shot.update_record(**valdict)

        redirect(request.env.http_referer)


def check_vAuth(vAuth):
    '''Check for vAuth'''
    vAuthdb = db(db.prefs.name == 'vAuth').select()
    for each in vAuthdb:
        if each.value == vAuth:
            return each.person


def upload_from_maya():
    '''Upload a video from maya'''

    vAuth = request.vars.auth
    uploader = check_vAuth(vAuth)
    if not uploader:
        return dict(result='Authentication Error')

    imgext = ['jpg', 'jpeg', 'tiff', 'tif', 'png', 'bmp']
    vidext = ['mpg', 'mp4', 'm4v', 'avi', 'flv', 'mov', '3gp', 'mkv']
    docext = ['pdf', 'txt', 'html']
    upload_folder = '%sstatic/uploads' % request.folder
    referer = request.env.http_referer
    prfile = request.vars.prfile
    thumb = request.vars.thumb
    frames = request.vars.frames
    cuts = request.vars.cuts
    st = request.vars.st  # maya start range of shot
    et = request.vars.et  # maya start range of shot
    scenePath = request.vars.scenePath  # maya start range of shot
    if not cuts:
        cuts = list()
    else:
        cuts = eval(cuts)
    filename = prfile.filename
    fid = uuid.uuid4()  # new file id
    shotuuid = request.vars.shotuuid
    sequuid = request.vars.sequuid
    #~ fd = 
    info = None
    fd = prfile.file
    tu = thumb.file  #thumbnal file
    #~ origname = request.vars.file.filename
    ext = filename.split('.')[-1].lower()
    sha1 =  request.vars.sha1
    tusha1 =  request.vars.tusha1
    dstpath = '%s/%s.%s' % (upload_folder, sha1, ext)
    tudstpath = '%s/%s.png' % (upload_folder, tusha1)
    #~ print fd, origname, ext
    dst = open(dstpath, 'wb')  # open a new file
    tudst = open(tudstpath, 'wb')  # open a new file for thumbnail
    shutil.copyfileobj(fd, dst)  # copy file
    shutil.copyfileobj(tu, tudst)  # copy thumb file
    dst.close()  # close it
    tudst.close()  # close it
    # add to db
    oldfile = db(db.vfile.hash == sha1).select().first()
    tuoldfile = db(db.vfile.uuid == tusha1).select().first()
    if not tuoldfile:
        newtuoldfile = db.vfile.insert(uuid=tusha1, ext='png')
    else:
        newtuoldfile = tuoldfile


    if not oldfile:  # file is new
        process = db.process.insert(isfinished=True, name=os.path.basename(dstpath)) #  define new process
        newfile = db.vfile.insert(process=process, hash=sha1, rawname=filename, \
            cuts=cuts, uuid=fid, ext=ext, name=os.path.basename(dstpath), isvideo=True)
    else:  # if file is old
        if not oldfile.process:  #if file hasent any process
            process = db.process.insert(isfinished=True) # this file do not need any extra process
            oldfile.update_record(isvideo=True, process=process)
        else:
            oldfile.process.update_record(isfinished=True)
        oldfile.update_record(cuts=cuts)

        newfile = oldfile
    if shotuuid and shotuuid != 'None':
        target = db(db.shot.uuid == shotuuid).select().first()  # find target shot database
        if not target:
            return dict(result='Error', info='Shot is not available!')
        target.update_record(frames=int(float(frames)), preview=newfile, \
                modification_date=dt.now(), thumb=newtuoldfile, dirty=True,
                startrange=int(st), endrange=int(et))
        target.sequence.update_record(dirty=True, ignore_shots=False)
        target.sequence.project.update_record(dirty=True)
        target.update_record(preview=newfile)
        info = 'Shot uploaded'

    elif sequuid and sequuid != 'None':
        target = db(db.sequence.uuid == sequuid).select().first()  # find target shot database
        if not target:
            return dict(result='Error', info='Sequence is not available!')
        if cuts:
            shots = db(db.shot.sequence==target).select()
            numOfShots = len(shots)
            while numOfShots < len(cuts):
                newshot = db.shot.insert(number=numOfShots + 1, \
                        supervisor=target.supervisor, sequence=target,\
                        uuid=uuid.uuid4())
                numOfShots+=1
      
        target.update_record(frames=int(float(frames)), preview=newfile, \
                ignore_shots=True, modification_date=dt.now(), \
                thumb=newtuoldfile, dirty=True)
        target.project.update_record(dirty=True)
        info = 'Sequence uploaded, cuts=%s' % cuts

    return dict(vname=newfile.name, shotuuid=shotuuid, sequuid=sequuid, \
            info='Thank you %s! %s.' % (uploader.first_name, info), result='ok')


def setPathSeqDataJSON():
    '''This function sets scene path information for a sequence'''
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        sid = request.vars.sid
        scenePath = request.vars.scenePath
        seq = db(db.sequence.uuid == sid).select().first()
        if scenePath:
            seq.update_record(scenePath=scenePath)
            return dict(result='ok')
        else:
            return dict(result='error', info='You must save your scene file before assigning it.')
    else:
        return dict(result='Authentication Error')

def setPathShotDataJSON():
    '''This function sets scene path information for a sequence'''
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        shotid = request.vars.shotid
        scenePath = request.vars.scenePath
        shot = db(db.shot.uuid == shotid).select().first()
        if scenePath:
            shot.update_record(scenePath=scenePath)
            return dict(result='ok')
        else:
            return dict(result='error', info='You must save your scene file before assigning it.')
    else:
        return dict(result='Authentication Error')

def getProjectsDataJSON():
    '''This function must be used as json data'''
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        projects = db(db.project.id).select(db.project.id, db.project.name)
        return dict(projects=projects, result='ok')
    else:
        return dict(result='Authentication Error')
    
def getSeqsDataJSON():
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        pr = request.vars.pr
        seqs = db(db.sequence.project == pr).select(db.sequence.number, db.sequence.uuid, orderby = db.sequence.number)
        return dict(seqs=seqs, result='ok')
    else:
        return dict(result='Authentication Error')


def getShotsDataJSON():
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        seq = request.vars.seq
        prid = request.vars.prid
        seq = db((db.sequence.number == seq) & (db.sequence.project==prid)).select().first()
        shots = db(db.shot.sequence == seq).select(db.shot.number, \
                db.shot.uuid, orderby = db.shot.number)
        return dict(shots=shots, result='ok')
    else:
        return dict(result='Authentication Error')

def getShotUUID():
    '''JSON - Get a shot uuid based on project name and sequence and shot numbers'''
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        prid = request.vars.prid
        seqnum = request.vars.seqnum
        shotnum = request.vars.shotnum
        seq = db( (db.sequence.project == prid) & \
                (db.sequence.number == seqnum) ).select(db.sequence.id).first()
        #return dict(seq=seq)
        target = db((db.shot.sequence==seq) & \
                (db.shot.number==shotnum) ).select(db.shot.uuid).first()
        return dict(shot=target.uuid, result='ok')
    else:
        return dict(result='Authentication Error')

def getSeqUUID():
    '''JSON - Get a seq uuid based on project name and sequence number'''
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        prid = request.vars.prid
        seqnum = request.vars.seqnum
        seq = db( (db.sequence.project == prid) & (db.sequence.number == seqnum) ).select(db.sequence.uuid).first()
        if seq:
            return dict(seq=seq.uuid, result='ok')
    else:
        return dict(result='Authentication Error')

def getShotInfoFromUUID():
    '''JSON - get shot information based on a given uuid'''
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        shotuuid = request.vars.uuid
        shot = db(db.shot.uuid == shotuuid).select(db.shot.number, \
                db.shot.sequence, db.shot.preview).first()
        if shot:
            preview = None
            if shot.preview:
                preview = shot.preview.name
            return dict(number=shot.number, mayafps=shot.sequence.project.mayafps, fps=shot.sequence.project.fps, seq=shot.sequence.number,\
                    pr=shot.sequence.project.name, preview=preview, result='ok')
        else:
            return dict(result='Error', info='Shot is not available on server.')
    else:
        return dict(result='Authentication Error')

def getSeqInfoFromUUID():
    '''JSON - get sequence information based on a given uuid'''
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        sequuid = request.vars.uuid
        seq = db(db.sequence.uuid == sequuid).select(db.sequence.number, \
                db.sequence.id, db.sequence.project, db.sequence.preview).first()
        if seq:
            preview = None
            shots = db(db.shot.sequence==seq).select(db.shot.uuid, db.shot.number)
            if seq.preview:
                preview = seq.preview.name
            return dict(numOfShots=len(shots), mayafps=seq.project.mayafps, fps=seq.project.fps,  shots=shots, number=seq.number, pr=seq.project.name, \
                    preview=preview, result='ok')
        else:
            return dict(result='Error', info='Sequence is not available on server.')
    else:
        return dict(result='Authentication Error')

def getScenePathJSON():
    '''Get a scene path'''
    prid = request.vars.prid
    seqNum = request.vars.seqNum
    #return seqNum
    shotNum = request.vars.shotNum
    if shotNum == 'None':
        shotNum = None
    prdb = db(db.project.id == prid).select(db.project.id).first()
    #return prdb
    seq = db((db.sequence.number == seqNum) & (db.sequence.project == prdb)).select(db.sequence.id, db.sequence.scenePath).first()
    #return seq
    if shotNum:
        shot = db((db.shot.number == shotNum) & (db.shot.sequence == seq)).select(db.shot.scenePath).first()
        return dict(scenePath=shot.scenePath, result='ok')
    else:
        return dict(scenePath=seq.scenePath, result='ok')


def createShot():
    vAuth = request.vars.auth
    if check_vAuth(vAuth):
        sid = request.vars.sid
        seq = db(db.sequence.uuid == sid).select().first()
        shots = db(db.shot.sequence==seq).select(db.shot.uuid)
        numOfShots = len(shots)
        newshot = db.shot.insert(number=numOfShots + 1, \
                supervisor=seq.supervisor, sequence=seq,\
                uuid=uuid.uuid4())
        return dict(result='ok', shotuuid=newshot.uuid, info='shot %s created and referenced to sequence %s' % (newshot.number, seq.number))
    else:
        return dict(result='Authentication Error')

def settings():
    '''Vixen server user settings'''
    vAuth = None
    vAuthdb = db((db.prefs.name=='vAuth') & (db.prefs.person==auth.user_id)).select().first()
    if vAuthdb:
        vAuth = vAuthdb.value
    return dict(vAuth=vAuth)

def do_save_settings():
    '''Save settings'''
    vAuth = request.vars.vAuth
    if vAuth:
        vAuthdb = db((db.prefs.name=='vAuth') & (db.prefs.person==auth.user_id)).select().first()
        if not vAuthdb:
            vAuthdb = db.prefs.insert(name='vAuth', value=vAuth)
        else:
            vAuthdb.update_record(value=vAuth)

    redirect(request.env.http_referer)

def downloads():
    return dict()

def status():
    '''Show status of running processes'''
    return dict()

def pMonitor():
    '''monitor a process on server'''
    appname = request.vars.appname
    execfn = 'ps -C %s' % appname
    p = Popen(execfn, shell=True, env=os.environ,
                  stdout=PIPE, universal_newlines=True)  # process
    data, error = p.communicate()
    return data

def delete_vfile():
    '''delete a file from database'''
    vuuid = request.vars.uuid
    vfile = db(db.vfile.uuid==vuuid).select(db.vfile.uuid, db.vfile.id).first()
    item = db(db.item.pid == request.vars.pid).select().last()
    newlist = [i for i in item.vfiles if i!=vfile.id]
    item.update_record(vfiles=newlist)

    return '''
        <script>
           location.reload();
        </script>

    '''
def rename_vfile():
    '''delete a file from database'''
    vuuid = request.vars.uuid
    rawname = request.vars.rawname
    thatfile = db(db.vfile.uuid==vuuid).select(db.vfile.id, db.vfile.uuid, db.vfile.rawname, db.vfile.ext).first()
    ext = thatfile.ext
    newname = '%s.%s' % (rawname, ext)
    #return newname
    #return thatfile.rawname
    #item = db(db.item.pid == request.vars.pid).select().last()
    #newlist = [i for i in item.vfiles if i!=vfile.id]
    thatfile.update_record(rawname=newname)

    return '''
        <script>
           location.reload();
        </script>

    '''

def vfile_comments():
    '''vfile comments page'''
    vuuid = request.vars.uuid
    vfile = db(db.vfile.uuid==vuuid).select().last()
    if vfile:
        upf = '%sstatic/uploads' % request.folder
        path = '%s/%s' % (upf, vfile.name)
        return dict(vfile=vfile, path=path)
    else:
        redirect(request.env.http_referer)
    #item = vfile.item
    #if not item:
    #item = db.item.insert(type='sdf')

    #return vuuid

def member_management():
    #return request.vars.project
    pid = request.vars.project
    #return pid
    project = db(db.project.id==pid).select(db.project.id, db.project.uuid, db.project.owner).first()
    members = request.vars.members
    users=db(db.auth_user.id).select(db.auth_user.id)
    gname = 'pr-%s' % project.uuid
    gid = auth.id_group(gname)
    for i in users:
        auth.del_membership(gid, i.id)
        if str(i.id) in members:
            auth.add_membership(gid, i.id)

    auth.add_membership(gid, project.owner)
    return '''
        <script>
           location.reload();
        </script>

    '''

def drop():
    item = request.vars.item
    #return item.uuid
    return dict(item=item)


def search_attachments():
    itemuuid = request.vars.itemuuid
    query = request.vars.attach_query
    upfolder = '%sstatic/uploads' % request.folder
    item = db(db.item.uuid == itemuuid).select().last()
    attachs = item.vfiles
    attachments = [db(db.vfile.id==i).select().first() for i in item.vfiles]
    result = []
    for attach in attachments:
        if query == None:
            result.append(attach.uuid)
        if query in attach.rawname:
            result.append(attach.uuid)
        if query in attach.uploader.first_name.lower():
            result.append(attach.uuid)
        if query in attach.uploader.last_name.lower():
            result.append(attach.uuid)
        if attach.ext == 'docx':
            frpath = '%s/%s' % (upfolder, attach.name)
            fpath = os.path.abspath(frpath)
            if os.path.isfile(fpath):
                document = docx.opendocx(fpath)
                paratextlist = docx.getdocumenttext(document)
                newparatextlist = []
                for paratext in paratextlist:
                    newparatextlist.append(paratext.encode("utf-8"))
                data=''.join(newparatextlist)
                if query in data:
                    result.append(attach.uuid)

    js = ''.join(["$('#{}').fadeIn();".format(i) for i in result])
    #return js
    return '''
        <script>
            $('.attach_files_list').children('LI').fadeOut();
            {}
        </script>
        '''.format(js)
