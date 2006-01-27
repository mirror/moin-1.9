# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Formatter Base Class

    @copyright: 2000 - 2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
import re, types

class FormatterBase:
    """ This defines the output interface used all over the rest of the code.

        Note that no other means should be used to generate _content_ output,
        while navigational elements (HTML page header/footer) and the like
        can be printed directly without violating output abstraction.
    """

    hardspace = ' '

    def __init__(self, request, **kw):
        self.request = request
        self._ = request.getText

        self._store_pagelinks = kw.get('store_pagelinks', 0)
        self._terse = kw.get('terse', 0)
        self.pagelinks = []
        self.in_p = 0
        self.in_pre = 0
        self._highlight_re = None
        self._base_depth = 0

    def set_highlight_re(self, hi_re=None):
        if type(hi_re) in [types.StringType, types.UnicodeType]:
            try:
                self._highlight_re = re.compile(hi_re, re.U + re.IGNORECASE)
            except re.error:
                hi_re = re.escape(hi_re)
                self._highlight_re = re.compile(hi_re, re.U + re.IGNORECASE)
        else:
            self._highlight_re = hi_re

    def lang(self, on, lang_name):
        return ""

    def setPage(self, page):
        self.page = page

    def sysmsg(self, on, **kw):
        """ Emit a system message (embed it into the page).

            Normally used to indicate disabled options, or invalid markup.
        """
        return ""

    # Document Level #####################################################
    
    def startDocument(self, pagename):
        return ""

    def endDocument(self):
        return ""

    def startContent(self, content_id="content", **kwargs):
        return ""

    def endContent(self):
        return ""

    # Links ##############################################################
    
    def pagelink(self, on, pagename='', page=None, **kw):
        """ make a link to page <pagename>. Instead of supplying a pagename,
            it is also possible to give a live Page object, then page.page_name
            will be used.
        """
        if not self._store_pagelinks or not on or kw.get('generated'): 
            return ''
        if not pagename and page:
            pagename = page.page_name
        pagename = self.request.normalizePagename(pagename)
        if pagename and pagename not in self.pagelinks:
            self.pagelinks.append(pagename)

    def interwikilink(self, on, interwiki='', pagename='', **kw):
        # call pagelink() for internal interwikilinks
        # to make shure they get counted for self.pagelinks
        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, '%s:%s' % (interwiki, pagename))
        if wikitag=='Self' or wikitag==self.request.cfg.interwikiname:
            if wikitail.find('#') > -1:
                wikitail, kw['anchor'] = wikitail.split('#', 1)
                wikitail = wikiutil.url_unquote(wikitail)
            return self.pagelink(on, wikitail, **kw)
        return ''
            
    def url(self, on, url=None, css=None, **kw):
        raise NotImplementedError

    # Attachments ######################################################

    def attachment_link(self, url, text, **kw):
        raise NotImplementedError
    def attachment_image(self, url, **kw):
        raise NotImplementedError
    def attachment_drawing(self, url, text, **kw):
        raise NotImplementedError

    def attachment_inlined(self, url, text, **kw):
        from MoinMoin.action import AttachFile
        import os
        _ = self.request.getText
        pagename, filename = AttachFile.absoluteName(url, self.page.page_name)
        fname = wikiutil.taintfilename(filename)
        fpath = AttachFile.getFilename(self.request, pagename, fname)
        base, ext = os.path.splitext(filename)
        Parser = wikiutil.getParserForExtension(self.request.cfg, ext)
        if Parser is not None:
            try:
                content = file(fpath, 'r').read()
                # Try to decode text. It might return junk, but we don't
                # have enough information with attachments.
                content = wikiutil.decodeUnknownInput(content)
                colorizer = Parser(content, self.request)
                colorizer.format(self)
            except IOError:
                pass

        return self.attachment_link(url, text)


    def anchordef(self, name):
        return ""

    def line_anchordef(self, lineno):
        return ""

    def anchorlink(self, on, name='', id=None):
        return ""

    def line_anchorlink(self, on, lineno=0):
        return ""

    def image(self, **kw):
        """ Take HTML <IMG> tag attributes in `attr`.

        Attribute names have to be lowercase!
        """
        attrstr = u''
        for attr, value in kw.items():
            if attr=='html_class':
                attr='class'
            attrstr = attrstr + u' %s="%s"' % (attr, wikiutil.escape(value))
        return u'<img%s>' % attrstr

    def smiley(self, text):
        return text

    def nowikiword(self, text):
        return self.text(text)

    # Text and Text Attributes ########################################### 
    
    def text(self, text):
        if not self._highlight_re:
            return self._text(text)
            
        result = []
        lastpos = 0
        match = self._highlight_re.search(text)
        while match and lastpos < len(text):
            # add the match we found
            result.append(self._text(text[lastpos:match.start()]))
            result.append(self.highlight(1))
            result.append(self._text(match.group(0)))
            result.append(self.highlight(0))

            # search for the next one
            lastpos = match.end() + (match.end() == lastpos)
            match = self._highlight_re.search(text, lastpos)

        result.append(self._text(text[lastpos:]))
        return ''.join(result)

    def _text(self, text):
        raise NotImplementedError

    def strong(self, on):
        raise NotImplementedError

    def emphasis(self, on):
        raise NotImplementedError

    def underline(self, on):
        raise NotImplementedError

    def highlight(self, on):
        raise NotImplementedError

    def sup(self, on):
        raise NotImplementedError

    def sub(self, on):
        raise NotImplementedError

    def strike(self, on):
        raise NotImplementedError

    def code(self, on, **kw):
        raise NotImplementedError

    def preformatted(self, on):
        self.in_pre = on != 0

    def small(self, on):
        raise NotImplementedError

    def big(self, on):
        raise NotImplementedError

    # special markup for syntax highlighting #############################

    def code_area(self, on, code_id, **kwargs):
        raise NotImplementedError

    def code_line(self, on):
        raise NotImplementedError

    def code_token(self, tok_text, tok_type):
        raise NotImplementedError

    # Paragraphs, Lines, Rules ###########################################

    def linebreak(self, preformatted=1):
        raise NotImplementedError

    def paragraph(self, on):
        self.in_p = (on != 0)

    def rule(self, size=0):
        raise NotImplementedError

    def icon(self, type):
        return type

    # Lists ##############################################################

    def number_list(self, on, type=None, start=None):
        raise NotImplementedError

    def bullet_list(self, on):
        raise NotImplementedError

    def listitem(self, on, **kw):
        raise NotImplementedError

    def definition_list(self, on):
        raise NotImplementedError

    def definition_term(self, on, compact=0):
        raise NotImplementedError

    def definition_desc(self, on):
        raise NotImplementedError

    def heading(self, on, depth, **kw):
        raise NotImplementedError

    # Tables #############################################################
    
    def table(self, on, attrs={}):
        raise NotImplementedError

    def table_row(self, on, attrs={}):
        raise NotImplementedError

    def table_cell(self, on, attrs={}):
        raise NotImplementedError

    # Dynamic stuff / Plugins ############################################
    
    def macro(self, macro_obj, name, args):
        # call the macro
        return macro_obj.execute(name, args)    

    def _get_bang_args(self, line):
        if line[:2]=='#!':
            try:
                name, args = line[2:].split(None, 1)
            except ValueError:
                return ''
            else:
                return args
        return None

    def processor(self, processor_name, lines, is_parser = 0):
        """ processor_name MUST be valid!
            writes out the result instead of returning it!
        """
        if not is_parser:
            processor = wikiutil.importPlugin(self.request.cfg, "processor",
                                              processor_name, "process")
            processor(self.request, self, lines)
        else:
            parser = wikiutil.importPlugin(self.request.cfg, "parser",
                                           processor_name, "Parser")
            args = self._get_bang_args(lines[0])
            if args is not None:
                lines=lines[1:]
            p = parser('\n'.join(lines), self.request, format_args = args)
            p.format(self)
            del p
        return ''

    def dynamic_content(self, parser, callback, arg_list = [], arg_dict = {},
                        returns_content = 1):
        content = parser[callback](*arg_list, **arg_dict)
        if returns_content:
            return content
        else:
            return ''

    # Other ##############################################################
    
    def rawHTML(self, markup):
        """ This allows emitting pre-formatted HTML markup, and should be
            used wisely (i.e. very seldom).

            Using this event while generating content results in unwanted
            effects, like loss of markup or insertion of CDATA sections
            when output goes to XML formats.
        """

        import formatter, htmllib
        from MoinMoin.util import simpleIO

        # Regenerate plain text
        f = simpleIO()
        h = htmllib.HTMLParser(formatter.AbstractFormatter(formatter.DumbWriter(f)))
        h.feed(markup)
        h.close()

        return self.text(f.getvalue())

    def escapedText(self, on):
        """ This allows emitting text as-is, anything special will
            be escaped (at least in HTML, some text output format
            would possibly do nothing here)
        """
        return ""

    def comment(self, text):
        return ""
