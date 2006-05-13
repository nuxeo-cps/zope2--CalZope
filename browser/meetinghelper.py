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

from datetime import datetime, timedelta, time

from zope.interface import Interface, implements
from zope.schema import Date
from zope.app.form.interfaces import WidgetInputError, MissingInputError
from zope.app.form.utility import setUpEditWidgets, applyWidgetsChanges
from zope.app import zapi
from zope.i18n import translate

from Products.Five.form import EditView

from calcore.schema import Timedelta, Time
from calcore.interfaces import IStorageManager
from Products.CalZope.interfaces import IZopeAttendeeSource

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")

class IMeetingHelper(Interface):
    """Just a little schema, so that we can use widgets"""
    
    begindate = Date(
        title=_("First date"),
        description=_("Start searching from this date."))

    enddate = Date(
        title=_("Last date"),
        description=_("Stop searching after this date."))

    fromhour = Time(
        title=_("Search between"),
        description=_("Start search at this hour"))
        
    tohour = Time(
        title=_("and"),
        description=_("Stop search at this hour"))
    
    duration = Timedelta(
        title=_("Duration"),
        description=_("The expected duration of the event"))

class MeetingHelper(object):

    implements(IMeetingHelper)
    
    def __init__(self):
        self.begindate = datetime.now()
        self.enddate = datetime.now() + timedelta(7)
        self.fromhour = time(10,0)
        self.tohour = time(17, 0)
        self.duration = timedelta(hours=1)


class MeetingHelperView(EditView):
    
    fieldNames = ('begindate', 'enddate', 'fromhour', 'tohour', 'duration')
        
    def __init__(self, context, request):
        self.helper = MeetingHelper()
        EditView.__init__(self, context, request)

    def _setUpWidgets(self):
        setUpEditWidgets(self, IMeetingHelper, self.helper) 

    #def widgets(self):
        #return [getattr(self, name+'_widget')
                #for name in self.fieldNames]
    
    def update(self):
        applyWidgetsChanges(self, IMeetingHelper, self.helper)
        
        attendee_source = self._getAttendeeSource()
        form = self.request.form
        
        # First fetch the search query:
        if 'UPDATE_USER_SEARCH' in form: # New search performed
            self.use_query = form['search_query']
        elif 'use_query' in form: # No new search, but an old one.
            self.use_query = form['use_query']
        else:
            self.use_query = ''
        
        # Do any actions
        if 'UPDATE_REMOVE' in form:
            removes = [key for key in form.keys() if key.startswith('remove_')]
            self.removeAttendees(removes)
        elif 'UPDATE_ADD' in form:
            adds = [key for key in form.keys() if key.startswith('add_')]
            self.inviteAttendees(adds)
        elif 'UPDATE_SEARCH_FREETIME' in form:
            self.getFreePeriods()
    
    def _getAttendeeSource(self):
        return zapi.getUtility(IZopeAttendeeSource, context=self.context)

    def _getStorageManager(self):
        return zapi.getUtility(IStorageManager, context=self.context)

    def _getAttendeeList(self):
        thiscal = self.getMainAttendeeId()
        return self.request.SESSION.get('meeting_helper_attendees', [thiscal])

    def _setAttendeeList(self, value):
        self.request.SESSION['meeting_helper_attendees'] = value
        
    def getAttendees(self):
        attendees =  self._getAttendeeList()
        return [self._getAttendeeSource().getAttendee(id) for id in attendees]

    def getMainAttendeeId(self):
        return self.context.getCalendar().getMainAttendee().getAttendeeId()

    def getSearchResults(self):
        attendee_source = self._getAttendeeSource()
        result = attendee_source.findByName(self.use_query)
        attendees = self._getAttendeeList()
        # Filter out the ones that exist already
        res =  [x for x in result if x.getId() not in attendees]
        return res
        
    def removeAttendees(self, removes):
        list = self._getAttendeeList()
        for id in removes:
            id = id[len('remove_'):]
            if id in list:
                list.remove(id)
        self._setAttendeeList(list)

    def inviteAttendees(self, adds):
        # Remove prefix
        list = self._getAttendeeList()
        for id in adds:
            id = id[len('add_'):]
            if not id in list:
                list.append(id)
        self._setAttendeeList(list)
        
    def getFreePeriods(self):
        storage = self._getStorageManager()
        attendees = self.getAttendees()
        # getFreePeriods see the end date as not inclusive, but the users
        # expected to be included, so a day is added on here.
        period = (self.helper.begindate, self.helper.enddate + timedelta(1))
        time = (self.helper.fromhour, self.helper.tohour)
        # XXX it would probably be a good idea to split the periods into 
        # segments that are as long as self.helper.duration
        self.free_periods = storage.getFreePeriods(attendees, period, time, 
                                                   self.helper.duration)

    def makeTimeUrl(self, dtstart, duration):
        dtend = dtstart + duration
        return "field.dtstart=%s&field.dtstart_hour=%s&field.dtstart_minute=" \
               "%s&field.dtend=%s&field.dtend_hour=%s&field.dtend_minute=%s" % (
                self.date2str(dtstart.date()), dtstart.hour, dtstart.minute, 
                self.date2str(dtend.date()), dtend.hour, dtend.minute)

    def getDateFormat(self):
        fmt = translate(_('%Y-%m-%d'), context=self.request, default='%Y-%m-%d')
        return str(fmt)
        
    def date2str(self, date):
        return date.strftime(str(self.getDateFormat()))

    def datetime2str(self, datetime):
        return datetime.strftime(str(self.getDateFormat() + ' %H:%M'))
