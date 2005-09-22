# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - email helper functions

    @copyright: 2003 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os

_transdict = {"AT": "@", "DOT": ".", "DASH": "-"}


def sendmail(request, to, subject, text, **kw):
    """ Create and send a text/plain message
        
    Return a tuple of success or error indicator and message.
    
    @param request: the request object
    @param to: recipients (list)
    @param subject: subject of email (unicode)
    @param text: email body text (unicode)
    @keyword mail_from: override default mail_from (string)
    @rtype: tuple
    @return: (is_ok, Description of error or OK message)
    """
    import smtplib, socket
    from email.MIMEText import MIMEText
    from email.Utils import formatdate
    from email.Header import Header
    from email.Utils import make_msgid
    
    from MoinMoin import config

    _ = request.getText
    cfg = request.cfg    
    mail_from = kw.get('mail_from', '') or cfg.mail_from

    # Create a text/plain message body (see RFC2822)
    # Replace LF with CRLF, encode using config.charset.
    text = text.replace(u'\n', u'\r\n')
    text = text.encode(config.charset)
    msg = MIMEText(text, 'plain', config.charset)
    
    # Create message headers
    msg['From'] = mail_from
    # Don't expose emails addreses of the other subscribers, instead we
    # use the same mail_from, e.g. "My Wiki <noreply@mywiki.org>"
    msg['To'] = mail_from
    msg['Date'] = formatdate()
    msg['Message-ID'] = make_msgid()
    msg['Subject'] = Header(subject, config.charset)
    if cfg.mail_sendmail:
        # Set the BCC.  This will be stripped later by sendmail.
        msg['BCC'] = ','.join(to)
        # Set Return-Path so that it isn't set (generally incorrectly) for us.
        msg['Return-Path'] = mail_from

    # Send the message
    if not cfg.mail_sendmail:
        try:
            server = smtplib.SMTP(cfg.mail_smarthost)
            try:
                #server.set_debuglevel(1)
                if cfg.mail_login:
                    user, pwd = cfg.mail_login.split()
                    try: # try to do tls
                        server.ehlo()
                        if server.has_extn('starttls'):
                            server.starttls()
                            server.ehlo()
                    except:
                        pass
                    server.login(user, pwd)
                server.sendmail(mail_from, to, msg.as_string())
            finally:
                try:
                    server.quit()
                except AttributeError:
                    # in case the connection failed, SMTP has no "sock" attribute
                    pass
        except smtplib.SMTPException, e:
            return (0, str(e))
        except (os.error, socket.error), e:
            return (0, _("Connection to mailserver '%(server)s' failed: %(reason)s") % {
                'server': cfg.mail_smarthost, 
                'reason': str(e)
            })
    else:
        try:
            sendmailp = os.popen(cfg.mail_sendmail, "w") 
            # msg contains everything we need, so this is a simple write
            sendmailp.write(msg.as_string())
            sendmail_status = sendmailp.close()
            if sendmail_status:
                return (0, str(sendmail_status))
        except:
            return (0, _("Mail not sent"))

    return (1, _("Mail sent OK"))


def decodeSpamSafeEmail(address):
    """ Decode obfuscated email address to standard email address

    Decode a spam-safe email address in `address` by applying the
    following rules:
    
    Known all-uppercase words and their translation:
        "DOT"   -> "."
        "AT"    -> "@"
        "DASH"  -> "-"

    Any unknown all-uppercase words simply get stripped.
    Use that to make it even harder for spam bots!

    Blanks (spaces) simply get stripped.
    
    @param address: obfuscated email address string
    @rtype: string
    @return: decoded email address
    """
    email = []

    # words are separated by blanks
    for word in address.split():
        # is it all-uppercase?
        if word.isalpha() and word == word.upper():
            # strip unknown CAPS words
            word = _transdict.get(word, '')
        email.append(word)

    # return concatenated parts
    return ''.join(email)

