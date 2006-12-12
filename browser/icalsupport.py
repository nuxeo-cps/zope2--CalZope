# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$

from Products.Five import BrowserView

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")

win_to_latin9 = { # below are cp1252 codes
    0x201a: u',',    # 0x82 lower single quote
    0x201e: u'"',    # 0x84 lower double quote (german?)
    0x02c6: u'^',    # 0x88 small upper ^
    0x2039: u'<',    # 0x8b small <
    0x2018: u'`',    # 0x91 single curly backquote
    0x2019: u"'",    # 0x92 single curly quote
    0x201c: u'"',    # 0x93 double curly backquote
    0x201d: u'"',    # 0x94 double curly quote
    0x2013: u'\xad', # 0x96 small dash
    0x2014: u'-',    # 0x97 dash
    0x02dc: u'~',    # 0x98 upper tilda
    0x203a: u'>',    # 0x9b small >
    0x00b4: u"'",    # 0xb4 almost horizontal single quote
    0x2026: u'...',  # 0x85 dots in one char
}

def latin9_friendly_utf8(utf8_string):
    """Ensure the given utf8_string does not have offending characters"""
    # convert cp1252 characters that have a latin9 equivalent
    u = utf8_string.decode('utf-8')
    u = u.translate(win_to_latin9)

    # try to encode as latin9 with a tolerant error scheme
    latin9_string = u.encode('iso-8859-15', 'xmlcharrefreplace')

    # reencode the resulting latin9 string back to utf8
    return latin9_string.decode('iso-8859-15').encode('utf-8')


class ICalendarImportExportView(BrowserView):
    """Handle ICAL over WebDAV

    Imported events are made latin9 friendly by converting characters that
    cannot get encoded in iso-8859-15.
    """

    def importUpdate(self):
        if self.request.form.has_key('SUBMIT_IMPORT'):
            ical_text = self.request.form['file'].read()
            if ical_text == "":
                # Workaround for weird CPSSkins behaviour.
                # CPSSkins will for some reason render this page twice. 
                # It seems to do this with ALL pages, but in this case
                # it will cause problems.
                return
            self._import(ical_text, synchronize=0)
            self.request.form['portal_status_message'] = 'psm_file_uploaded'
            return

    def PUT(self, REQUEST, RESPONSE):
        """This is a PUT method.

        This docstring is unfortunately necessary for Zope 2 security
        reasons, otherwise the PUT method will not be found.
        This is because PUT is not called through Five directly,
        but through the Zope 2 Publisher.

        Permission is managed on a per event bases by the importer.
        """
        ical_text = REQUEST['BODYFILE'].read()
        synchronize = REQUEST.form.get('synchronize', 1)
        self._import(ical_text, synchronize=synchronize)
        RESPONSE.setStatus(204)
        return RESPONSE

    def _import(self, ical_text, synchronize=1):
        """Import an ICal string taking care of permissions on events"""
        ical_text = latin9_friendly_utf8(ical_text)
        calendar = self._getCalendar()
        calendar.import_(ical_text, synchronize=synchronize)

    def export(self):
        """Export to ICal format

        We cannot export this as an attribute directly, as to support
        PUT we apparently need to publish as a template.

        Takes care of hiding private event.
        """
        self.request.RESPONSE.setHeader(
            'Content-Type', 'text/calendar;charset=utf-8')
        calendar = self._getCalendar()
        ical = calendar.export()
        # XXX Zope 2.10 and later wants unicode here, but I'm not
        # sure that will work with 2.9, which needs support still.
        return ical.decode('utf-8')

    def _getCalendar(self):
        return self.context.aq_inner


class IDateImportExportView(ICalendarImportExportView):

    def _getCalendar(self):
        calendar = self.context.aq_inner.getCalendar()
        return calendar

