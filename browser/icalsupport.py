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

class ICalendarImportExportView(BrowserView):
    
    def importUpdate(self):
        if self.request.form.has_key('SUBMIT_IMPORT'):
            icalendar = self.request.form['file'].read()
            calendar = self._getCalendar()
            calendar.import_(icalendar)
            self.request.form['portal_status_message'] = 'psm_file_uploaded'
    
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
        icalendar = REQUEST['BODYFILE'].read()
        calendar = self._getCalendar()
        calendar.import_(icalendar, synchronize=1)
        RESPONSE.setStatus(204)
        return RESPONSE

class IDateImportExportView(ICalendarImportExportView):

    def _getCalendar(self):
        calendar = self.context.aq_inner.getCalendar()
        return calendar
    
