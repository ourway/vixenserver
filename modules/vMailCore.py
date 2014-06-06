#coding: UTF8
"""
mailer module

Simple front end to the smtplib and email modules,
to simplify sending email.

A lot of this code was taken from the online examples in the
email module documentation:
http://docs.python.org/library/email-examples.html

Released under MIT license.

Sample code:

import mailerCore

message = mailer.Message()
message.From = "me@example.com"
message.To = "you@example.com"
message.Subject = "My Vacation"
message.Body = open("letter.txt", "rb").read()
message.attach("picture.jpg")

mailer = mailer.Mailer('mail.example.com')
mailer.send(message)

"""
import smtplib
import time

# Import the email modules we'll need
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# For guessing MIME type based on file name extension
import mimetypes

from os import path

__version__ = "0.2"
__author__ = "Farsheed Ashouri"
__license__ = "MIT"

class Mailer(object):
    """
    Represents an SMTP connection.
    
    Use login() to log in with a username and password.
    """

    def __init__(self, host="localhost"):
        self.host = 'smtp.gmail.com'
        #self.port = 587
        self._usr = 'vixenserver@gmail.com'
        self._pwd = 'Cc183060'
    
    def login(self, usr, pwd):
        self._usr = usr
        self._pwd = pwd

    def send(self, msg):
        """
        Send one message or a sequence of messages.

        Every time you call send, the mailer creates a new
        connection, so if you have several emails to send, pass
        them as a list:
        mailer.send([msg1, msg2, msg3])
        """
        server = smtplib.SMTP(self.host)
        server.starttls()

        if self._usr and self._pwd:
            server.login(self._usr, self._pwd)

        try:
            for m in msg:
                self._send(server, m)
                time.sleep(5)
        except TypeError:
            self._send(server, msg)
            time.sleep(5)

        server.quit()
    
    def _send(self, server, msg):
        """
        Sends a single message using the server
        we created in send()
        """
        me = msg.From
        you = [x.split() for x in msg.To.split(",")]
        server.sendmail(me, you, msg.as_string())

class Message(object):
    """
    Represents an email message.
    
    Set the To, From, Subject, and Body attributes as plain-text strings.
    Optionally, set the Html attribute to send an HTML email, or use the
    attach() method to attach files.
    
    Even when sending an HTML email, you have to set the Body attribute as
    the alternative text version.
    
    Send using the Mailer class.
    """

    def __init__(self):
        self.attachments = []
        self._to = None
        self.Bcc = None
        self.From = None
        self.Subject = None
        self.Body = None
        self.Html = None

    def _get_to(self):
        addrs = self._to.replace(";", ",").split(",")
        return ", ".join([x.strip()
                          for x in addrs])
    def _set_to(self, to):
        self._to = to
    
    To = property(_get_to, _set_to,
                  doc="""The recipient(s) of the email.
                  Separate multiple recipients with commas or semicolons""")

    def as_string(self):
        """Get the email as a string to send in the mailer"""

        if not self.attachments:
            return self._plaintext()
        else:
            return self._multipart()
    
    def _plaintext(self):
        """Plain text email with no attachments"""

        if not self.Html:
            msg = MIMEText(self.Body)
        else:
            msg  = self._with_html()

        self._set_info(msg)
        return msg.as_string()
            
    def _with_html(self):
        """There's an html part"""

        outer = MIMEMultipart('alternative')
        
        part1 = MIMEText(self.Body, 'plain')
        part2 = MIMEText(self.Html, 'html')

        outer.attach(part1)
        outer.attach(part2)
        
        return outer

    def _set_info(self, msg):
        msg['Subject'] = self.Subject
        msg['From'] = self.From
        msg['To'] = self.To
        msg['Bcc'] = self.Bcc

    def _multipart(self):
        """The email has attachments"""

        msg = MIMEMultipart()
        
        msg.attach(MIMEText(self.Body, 'plain'))
        msg.attach(MIMEText(self.Html, 'html'))

        self._set_info(msg)
        msg.preamble = self.Subject

        for filename in self.attachments:
            self._add_attachment(msg, filename)
        return msg.as_string()

    def _add_attachment(self, outer, filename):
        ctype, encoding = mimetypes.guess_type(filename)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        fp = open(filename, 'rb')
        if maintype == 'text':
            # Note: we should handle calculating the charset
            msg = MIMEText(fp.read(), _subtype=subtype)
        elif maintype == 'image':
            msg = MIMEImage(fp.read(), _subtype=subtype)
        elif maintype == 'audio':
            msg = MIMEAudio(fp.read(), _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(fp.read())
            # Encode the payload using Base64
            encoders.encode_base64(msg)
        fp.close()
        # Set the filename parameter
        msg.add_header('Content-Disposition', 'attachment', filename=path.basename(filename))
        outer.attach(msg)

    def attach(self, filename, name=None):
        """
        Attach a file to the email. Specify the name of the file;
        Message will figure out the MIME type and load the file.
        """
        if not name:
            self.attachments.append(filename)
        else:
            self.attachments.append(filename, name)
