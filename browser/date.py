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
from datetime import datetime

from zope.app import zapi
from Products.Five import BrowserView

from calcore import cal
from calcore.interfaces import IAttendeeSource, IStorageManager

class DateView(BrowserView):
    
    def _attendee(self):
        return zapi.getUtility(IAttendeeSource, context=self.folder
                               ).getCurrentUserAttendee()
    
    def getCalendarUrl(self):
        return self.context.getCalendar().absolute_url()
    
    def meetingHelper(self):
        self.request.response.redirect(self.getCalendarUrl() + '/meetinghelper.html')
