# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - revert a page to a previous revision

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.Page import Page

def execute(pagename, request):
    """ restore another revision of a page as a new current revision """
    from MoinMoin.PageEditor import PageEditor
    rev = request.rev
    pg = PageEditor(request, pagename)

    try:
        msg = pg.revertPage(rev)
    except PageEditor.RevertError, error:
        msg = unicode(error)

    request.reset()
    pg.send_page(msg=msg)
