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

from datetime import datetime, timedelta

from AccessControl import getSecurityManager
from zope.app.form.utility import applyWidgetsChanges
from Products.Five.form import AddView
from Products.Five.browser.adding import ContentAdding
from Products.CalZope.interfaces import IDay, IWeek, IMonth
from calcore.interfaces import IAttendeeSource, IStorageManager
from zope.app import zapi

class CalendarEventAdding(ContentAdding):
    def add(self, content):
        # All the real work has been done in the factory already
        
        # Set unique id as an instance attribute in order for the 
        # AddingHelper to be able to construct an URL to the newly
        # created event
        self._event_unique_id = content.unique_id
        # Set the new default date for the view.
        self.request.SESSION['calzope_view_date'] = content.dtstart.date()
        return content

def EventFactory(view, id, title, dtstart, dtend, allday=False):
    duration = dtend - dtstart
    # If we're dealing with an event which ends before it starts.
    # The UI handles this so this should never happen, but in case 
    # somebody overrides the default widgets...
    if duration < timedelta(days=0):
        duration = timedelta(hours=1)
    cal = view.context.context.getCalendar()
    attendee = cal.getMainAttendee()
    # title and description will be set directly after add
    event = attendee.createEvent(dtstart=dtstart, duration=duration,
                                 allday=allday)
    # XXX acquisition context needed?
    return event.__of__(cal)

def MeetingFactory(view, id, title, dtstart, dtend, allday=False):
    event = EventFactory(view, id, title, dtstart, dtend, allday)
    attendees = view.request.SESSION.get('meeting_helper_attendees', [])
    asrc = zapi.getUtility(IAttendeeSource)
    currentuser = getSecurityManager().getUser()
    for attendeeid in attendees:
        attendee = asrc.getAttendee(attendeeid)
        event.attendees = event.invite([attendee])
        calendar = asrc.getMainCalendarForAttendeeId(attendeeid)
        if currentuser.has_permission('Manage participation status', calendar):
            event.setParticipationStatus(attendee, 'ACCEPTED')

   # Everything worked fine, clear the list of attendees:
    attendees = view.request.SESSION['meeting_helper_attendees'] = []
    return event
    
class AddingHelper(AddView):
    def nextURL(self):
        base = self.context.context.getCalendar().absolute_url()
        # _event_unique_id should be set by event adding object...
        return '%s/event/%s' % (base, self.context._event_unique_id)

    def _setUpWidgets(self):
        AddView._setUpWidgets(self)
        self.title_widget.displayWidth = 50
        self.description_widget.width = 48
        self.description_widget.height = 7
        self.location_widget.width = 30
        self.location_widget.height = 7
        self.categories_widget.width = 30
        self.categories_widget.height = 7

        if not (self.dtstart_widget.hasInput() and self.dtend_widget.hasInput()):
            view_object = self.context.context
            if IDay.providedBy(view_object):
                day = datetime(
                    view_object.getYear(),
                    view_object.getMonth(),
                    view_object.getDay())
            elif IWeek.providedBy(view_object):
                day = view_object.getDateForWeekday(1)
            elif IMonth.providedBy(view_object):
                day = datetime(view_object.getYear(), view_object.getMonth(), 1)
            else:
                day = datetime.now()
            
            if not self.dtstart_widget.hasInput():
                self.dtstart_widget.setRenderedValue(day)
            if not self.dtend_widget.hasInput():
                self.dtend_widget.setRenderedValue(day)
                                
