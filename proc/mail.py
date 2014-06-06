#!/usr/bin/python
#========== General Emailing system =============

# Imports
import os
import time
import uuid
import random
import sys
import vMailCore as mailer
#import html2text as ht
# definitions
message = mailer.Message()
message.From = "VixenServer Notification <farsheed.ashouri@gmail.com>"


def logger(msg, mtype):
    '''logging part'''
    with open('applications/vixenserver/proc/notofication.log', 'a') as log:
        log.writelines('%s - %s Notif: %s \n' % (str(time.ctime()), mtype, msg))


def process():
    '''This function searches database for email queues and process them'''
    processdb = db(db.process.name == 'mailer').select().first()
    #processdb.update_record(islocked=False)
    if not processdb:  # in case we haven't any mailer process
        processdb = db.process.insert(name='mailer', islocked=False)
    if not processdb.islocked:  # ok, the mailer system is free, now we can send emails
        try:
            emails = db(db.mail_queue.status == 'queue').select(orderby=db.mail_queue.priority)  # list of mails that not processed before
        except TypeError:  # when we can't read database with type error, probabaly there is an error whit migaration!
            db(db.mail_queue.id).delete()
            db.commit()
            print 'There was an error in database and all messages deleted.'
            return
        if len(emails):  # id there is any available email in queue:
            ##Start mail system
            processdb.update_record(islocked=True)  # lock the mailer system process
            db.commit()  # commit database for preventing other mailer process to access it.
            print('\n%s  Start to send %s email(s):\n' % (''.join(time.ctime().split()[3:-1]), len(emails)))
            trec = time.time()  # save the time
            for email in emails:  # start a send loop for each mail
                ##email.update_record(status='processing')
                ##TODO Need to add commit here...
                try:
                    message.To = email.email
                    message.Subject = '%s - %s' % (email.subject, ''.join(time.ctime().split()[:3]))  # message subject
                    message.Html = response.render('email_generic.html', mtype=email.mtype, body=email.mbody)
                    item = db(db.item.pid == email.message.uuid).select().first()
                    #print item
                    for i in item.vfiles:
                        fdb = db(db.vfile.id == i).select(db.vfile.name).first()
                        fpath = '%s/static/uploads/%s' % (request.folder, fdb.name)
                        attach = os.path.realpath(fpath)
                        if os.path.isfile(attach) and os.stat(attach)[6]/1000.0 < 1024:
                            message.attach(attach)
                            
                    meng = mailer.Mailer(email.email)  # specifying the client mail to mailer system
                    send = meng.send(message)  # send mail
                except Exception, e:  # if no connection or has error
                    if str(e) == "unhashable type: 'list'":  # if email is incorrect
                        #print '---%s---'%e
                        #print type(e)
                        email.update_record(status='sent')  # delete it from queue
                        db.commit()
                        print 'wrong email: %s - Deleted.' % email.email
                    else:
                        processdb.update_record(islocked=False)  # unlock mailer process
                        db.commit()  # commit changes to database
                        print('\n========\nAn error occured!\nThis is the error:\t%s\n========\n' % e)
                        return  # finish
                log_msg = '1 %s for %s' % (email.mtype, email.email)
                logger(log_msg, mtype=email.mtype)
                email.update_record(status='sent')
                db.commit()
                print('\t|* Email sent to: %s' % email.email)
            processdb.update_record(islocked=False)
            db.commit()
            print('\nFinished sending mail(s) in %s seconds.\n' % str(time.time() - trec))
        else:  # there is no mail in the queue:
            print('\nThere is no message is mail queue!\n')
            return
    else:  # processdb is locked
        print('\nMailer System is locked.\n')
        return
    #db(db.mail_queue.status == 'sent').delete()  # delete all sent messages from database
    #db.commit()  # Final commit for recording changes
    return  # end of process


if __name__ == '__main__':
    process()
