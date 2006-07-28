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
from AccessControl import getSecurityManager
from AccessControl import Unauthorized

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
            icalendar = self.request.form['file'].read()
            icalendar = latin9_friendly_utf8(icalendar)
            if icalendar == "":
                self.request.form['portal_status_message'] = 'Men vafan!'
                return "a"
            calendar = self._getCalendar()
            calendar.import_(icalendar)
            self.request.form['portal_status_message'] = 'psm_file_uploaded'
            return "b"

    def _getCalendar(self):
        return self.context.aq_inner

    def export(self):
        """
        Export to icalendar format.

        We cannot export this as an attribute directly, as to support
        PUT we apparently need to publish as a template.
        """
        self.request.RESPONSE.setHeader(
            'Content-Type', 'text/calendar;charset=utf-8')
        calendar = self._getCalendar()
        return calendar.export()

    def PUT(self, REQUEST, RESPONSE):
        """This is a PUT method.

        This docstring is unfortunately necessary for Zope 2 security
        reasons, otherwise the PUT method will not be found.
        This is because PUT is not called through Five directly,
        but through the Zope 2 Publisher.
        """
        if not getSecurityManager().checkPermission(
            'Edit calendar', self.context):
            raise Unauthorized(self.__name__, self.context)

        icalendar = REQUEST['BODYFILE'].read()
        icalendar = latin9_friendly_utf8(icalendar)
        calendar = self._getCalendar()
        calendar.import_(icalendar, synchronize=1)
        RESPONSE.setStatus(204)
        return RESPONSE

class IDateImportExportView(ICalendarImportExportView):

    def _getCalendar(self):
        calendar = self.context.aq_inner.getCalendar()
        return calendar

