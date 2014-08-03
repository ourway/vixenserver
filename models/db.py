# -*- coding: utf-8 -*-
import uuid
import hashlib
import datetime
now=datetime.datetime.now()
location = 'dev'
#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

    ## if NOT running on Google App Engine use SQLite or other DB
#db = DAL('sqlite://storage.sqlite', check_reserved=['postgres', 'mssql'])
if not location == 'dev':
    db = DAL("postgres://vserver:pass@localhost:5432/vserver", \
        migrate=True, pool_size=10, check_reserved=['postgres', 'mssql'])
else:
    db = DAL('sqlite://storage.sqlite', check_reserved=['postgres', 'mssql'])
#db = DAL('mysql://root:Cc183060@localhost/vserver', pool_size=10, check_reserved=['postgres', 'mssql'])


'''
sudo apt-get -y install postgresql
sudo apt-get -y install python-psycopg2
sudo -u postgres createuser -PE vserver
sudo -u postgres createdb -O vserver -E UTF8 vserver
# configuring
sudo vim /etc/postgresql/9.1/main/postgresql.conf
#uncomment these lines:
track_counts = on
autovacuum = on # Enable autovacuum subprocess?
# Restarting it:
sudo /etc/init.d/postgresql-8.4 restart
'''

#db = DAL("postgres://vishka:Cc183060@localhost:5432/vixenserver", pool_size=10, check_reserved=['postgres', 'mssql'])
## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, hmac_key=Auth.get_or_create_key())
crud, service, plugins = Crud(db), Service(), PluginManager()
username=True

## create all tables needed by auth if not custom tables
auth.define_tables(migrate=True)

## configure email
mail=auth.settings.mailer
mail.settings.server = 'smtp.gmail.com:587'
mail.settings.sender = 'vixenserver@gmail.com'
mail.settings.login = 'vixenserver:Cc183060'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True




## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth,filename='private/janrain.key')


response.generic_patterns = ['*.json']

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

db.define_table('prefs',
    Field('datetime', 'datetime', default=now),
    Field('name', length=32),
    Field('value', length=356),
    Field('person', db.auth_user, default=auth.user_id),
    )

db.define_table('owner',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('pwd', length=64),
    Field('admin', db.auth_user, default=auth.user_id),
    )


db.define_table('process',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('name','string'),
    Field('islocked','boolean',default=False),
    Field('isfinished','boolean',default=False),
    Field('isreported','boolean',default=False),
    )


db.define_table('item',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('creation_date', 'datetime', default=now),
    Field('owner', db.auth_user, default=auth.user_id),
    Field('pid',  length=256),
    Field('type', length=32),
    Field('likes', 'list:reference auth_user', default=[]),
    Field('shared_with', 'list:reference auth_user', default=[]),
    Field('publish_code', length=64, default=uuid.uuid4()),
    Field('description','text'),
    Field('vfiles', 'list:reference vfile', default=[]),
    Field('type', length=64)
    )

db.define_table('vfile',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('datetime', 'datetime', default=now),
    Field('name', length=256),
    Field('type', length=32, default='file'),
    Field('rawname', length=256),
    Field('m4v', length=256), # for videos
    Field('mpg', length=256), # for videos
    Field('cache', length=256),
    Field('thumb', 'integer', default=None),  #for videos
    Field('ext', length=64),
    Field('hash', length=256),
    Field('frames', 'integer', default=0),
    Field('cuts', 'list:integer', default=[]),
    Field('data', 'blob'),
    Field('process', db.process),
    Field('uploader', db.auth_user, default=auth.user_id),
    Field('isvideo', 'boolean', default=False),
    Field('isreported','boolean',default=False),
    Field('item', db.item),
    Field('tags','list:string', default=[]),
    )


db.define_table('project',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('creation_date','datetime',default=now),
    Field('modification_date','datetime'),
    Field('name', length=128),
    Field('software_3d', length=128),
    Field('software_comp', length=128),
    Field('type', length=32, default='project'),
    Field('fps', 'integer', default=24),
    Field('mayafps', 'integer', default=24),
    Field('size', length=64, default='1280x720'),
    Field('frames', 'integer', default=0),
    Field('description', length=1024),
    Field('scenePath', length=512),
    Field('path', length=256),
    Field('supervisor', db.auth_user),
    Field('owner', db.auth_user),
    Field('td', db.auth_user),
    Field('director', db.auth_user),
    Field('producer', db.auth_user),
    Field('thumb', db.vfile),
    Field('chart1', db.vfile),
    Field('chart2', db.vfile),
    Field('qr', db.vfile),
    Field('preview', db.vfile),
    Field('previews', 'list:reference vfile', default=[]),
    Field('member', 'list:reference auth_user', default=[]),
    Field('progress', 'integer', default=0),
    Field('dirty', 'boolean', default=False),
    Field('isactive', 'boolean', default=True),
    Field('isreported','boolean',default=False),
    )



db.define_table('sequence',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('creation_date','datetime',default=now),
    Field('modification_date','datetime'),
    Field('number', 'integer'),
    Field('name', length=128),
    Field('type', length=32, default='sequence'),
    Field('description', length=1024),
    Field('scenePath', length=512),
    Field('project', db.project),
    Field('frames', 'integer', default=0),
    Field('shots', 'list:reference shot', default=[]),
    Field('supervisor', db.auth_user),
    Field('owner', db.auth_user),
    Field('thumb', db.vfile),
    Field('preview', db.vfile),
    Field('previews', 'list:reference vfile', default=[]),
    Field('member', 'list:reference auth_user', default=[]),
    Field('qr', db.vfile),
    Field('chart1', db.vfile),
    Field('chart2', db.vfile),
    Field('progress', 'integer', default=0),
    Field('dirty', 'boolean', default=False),
    Field('ignore_shots', 'boolean', default=False),
    Field('isreported','boolean',default=False),
    )

db.define_table('shot',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('creation_date','datetime',default=now),
    Field('modification_date','datetime'),
    Field('number', 'integer'),
    Field('type', length=32, default='shot'),
    Field('name', length=128),
    Field('frames', 'integer', default=0),
    Field('endrange', 'integer', default=0),
    Field('startrange', 'integer', default=0),
    Field('description', length=1024),
    Field('scenePath', length=512),
    Field('render_description', length=256),
    Field('animatic_desc', length=256),
    Field('layout_desc', length=256),
    Field('animation_desc', length=256),
    Field('lighting_desc', length=256),
    Field('rendering_desc', length=256),
    Field('preview_desc', length=256),
    Field('compositing_desc', length=256),
    Field('sequence', db.sequence),
    Field('assets', 'list:reference asset', default=[]),
    Field('member', 'list:reference auth_user', default=[]),
    Field('supervisor', db.auth_user),
    Field('owner', db.auth_user),
    Field('animatic_sup', db.auth_user),
    Field('layout_sup', db.auth_user),
    Field('animation_sup', db.auth_user),
    Field('lighting_sup', db.auth_user),
    Field('rendering_sup', db.auth_user),
    Field('preview_sup', db.auth_user),
    Field('compositing_sup', db.auth_user),
    Field('thumb', db.vfile),
    Field('qr', db.vfile),
    Field('chart1', db.vfile),
    Field('chart2', db.vfile),
    Field('preview', db.vfile),
    Field('previews', 'list:reference vfile', default=[]),
    Field('progress', 'integer', default=0),
    Field('characters', 'integer', default=0),
    Field('layout_complexity', 'integer', default=2),
    Field('animatic_complexity', 'integer', default=2),
    Field('animation_complexity', 'integer', default=2),
    Field('lighting_complexity', 'integer', default=2),
    Field('rendering_complexity', 'integer', default=2),
    Field('preview_complexity', 'integer', default=2),
    Field('compositing_complexity', 'integer', default=2),
    Field('dirty', 'boolean', default=False),
    Field('animatic_iswip', 'boolean', default=False),
    Field('layout_iswip', 'boolean', default=False),
    Field('animation_iswip', 'boolean', default=False),
    Field('lighting_iswip', 'boolean', default=False),
    Field('rendering_iswip', 'boolean', default=False),
    Field('preview_iswip', 'boolean', default=False),
    Field('compositing_iswip', 'boolean', default=False),
    Field('animatic_iswip_date','datetime'),
    Field('layout_iswip_date','datetime'),
    Field('animation_iswip_date','datetime'),
    Field('lighting_iswip_date','datetime'),
    Field('rendering_iswip_date','datetime'),
    Field('preview_iswip_date','datetime'),
    Field('compositing_iswip_date','datetime'),
    Field('animatic_iscompleted', 'boolean', default=False),
    Field('layout_iscompleted', 'boolean', default=False),
    Field('animation_iscompleted', 'boolean', default=False),
    Field('lighting_iscompleted', 'boolean', default=False),
    Field('rendering_iscompleted', 'boolean', default=False),
    Field('preview_iscompleted', 'boolean', default=False),
    Field('compositing_iscompleted', 'boolean', default=False),
    Field('animatic_iscompleted_date','datetime'),
    Field('layout_iscompleted_date','datetime'),
    Field('animation_iscompleted_date','datetime'),
    Field('lighting_iscompleted_date','datetime'),
    Field('preview_iscompleted_date','datetime'),
    Field('rendering_iscompleted_date','datetime'),
    Field('compositing_iscompleted_date','datetime'),
    Field('animatic_isconfirmed', 'boolean', default=False),
    Field('layout_isconfirmed', 'boolean', default=False),
    Field('animation_isconfirmed', 'boolean', default=False),
    Field('lighting_isconfirmed', 'boolean', default=False),
    Field('rendering_isconfirmed', 'boolean', default=False),
    Field('preview_isconfirmed', 'boolean', default=False),
    Field('compositing_isconfirmed', 'boolean', default=False),
    Field('fixed_cam', 'boolean', default=False),
    Field('animatic_isconfirmed_date','datetime'),
    Field('layout_isconfirmed_date','datetime'),
    Field('lighting_isconfirmed_date','datetime'),
    Field('animation_isconfirmed_date','datetime'),
    Field('preview_isconfirmed_date','datetime'),
    Field('rendering_isconfirmed_date','datetime'),
    Field('compositing_isconfirmed_date','datetime'),
    Field('isreported','boolean',default=False),
    )



db.define_table('asset',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('creation_date','datetime',default=now),
    Field('modification_date','datetime'),
    Field('name', length=128),
    Field('type', length=32, default='asset'),
    Field('description', length=1024),
    Field('scenePath', length=512),
    Field('supervisor', db.auth_user),
    Field('owner', db.auth_user),
    Field('thumb', db.vfile),
    Field('qr', db.vfile),
    Field('chart1', db.vfile),
    Field('chart2', db.vfile),
    Field('preview', db.vfile),
    Field('progress', 'integer', default=0),
    Field('shots', 'list:reference shot', default=[]),
    Field('member', 'list:reference auth_user', default=[]),
    Field('isreported','boolean',default=False),
    )


db.define_table('comment',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('creation_date', 'datetime', default=now),
    Field('body', 'text'),
    Field('actor',db.auth_user, default=auth.user_id),
    Field('likes','list:reference auth_user', default=[]),
    Field('item',db.item),
    Field('isreported','boolean',default=False),
    )


db.define_table('message',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('creation_date', 'datetime', default=now),
    Field('sender', db.auth_user, default=auth.user_id),
    Field('target', db.auth_user),
    Field('body', 'text'),
    Field('subject', length=64),
    Field('descr', length=128),
    Field('unread', 'boolean', default=True),
    Field('archive', 'boolean', default=False),
    Field('read_date', 'datetime'),
    Field('attachement', 'list:reference vfile', []),
    Field('isreported','boolean',default=False),
    )


db.define_table('mail_queue',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('email','string'),
    Field('subject','string'),
    Field('mtype','string', default='letter'),
    Field('mbody','blob'), #give body a blob for unlimited message size.
    Field('priority','integer', default=5), #importing messages like signup information are priority 1
    Field('status','string',default='queue'), # queue/processing/finished
    Field('attachement', 'list:reference vfile', []),
    Field('message', db.message),
    )


db.define_table('blog',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('title','string'),
    Field('body', 'blob'),
    Field('visitors', 'integer', default=1),
    Field('tags','list:string', default=[]),
    Field('category','list:string', default=['general']),
    Field('created', 'datetime', default=request.now),
    Field('modified', 'datetime', default=request.now),
    Field('creator', db.auth_user, default=auth.user_id),
    Field('disabled', 'integer'),
    Field('isreported','boolean',default=False),
    )

db.define_table('report',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('body', length=2048),
    Field('created', 'datetime', default=request.now),
    Field('creator', db.auth_user, default=auth.user_id),
    Field('isreported','boolean',default=False),
    )

db.define_table('note',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('title', length=128),
    Field('body', 'blob'),
    Field('tags', 'list:string', default=[]),
    Field('links', 'list:reference note', default=[]),
    Field('editable', 'list:reference auth_user', default=[auth.user_id]),
    Field('viewable', 'list:reference auth_user', default=[auth.user_id]),
    Field('attachments', 'list:reference vfile', default=[]),
    Field('created', 'datetime', default=request.now),
    Field('creator', db.auth_user, default=auth.user_id),
    Field('hidden','boolean', default=False),
    Field('isreported','boolean', default=False),
    )

db.define_table('gallery',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('created', 'datetime', default=now),
    Field('creator', db.auth_user, default=auth.user_id),
    Field('name', length=256),
    Field('photos', 'list:reference vfile', default=[]),
    Field('artwork', db.vfile),
    Field('description', 'text'),
    Field('hash', 'string', default=hashlib.md5(str(now)).hexdigest()),
    )

db.define_table('visitor',
    Field('uuid', length=64, default=uuid.uuid4()),
    Field('created', 'datetime', default=now),
    Field('ip', length=32, default=request.env.remote_addr),
    Field('item', db.item),
 )
