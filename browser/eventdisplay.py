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
"""
  eventposition.py
"""
from datetime import timedelta, datetime, time
from AccessControl import getSecurityManager

from zope.interface import implements
from zope.app import zapi

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")

from Products.CalZope.interfaces import IZopeAttendeeSource

from displaytable import DayGrid, Cell
from interfaces import IEventDisplay


# XXX This is reused in several places by copy/paste.
# Some sort of refactoring here would be good.
def checkPermission(permission, object):
    user = getSecurityManager().getUser()
    return user.has_permission(permission, object)


class EventDisplay(Cell):
    """Adapts en event to IEventDisplay
    """
    
    implements(IEventDisplay)

    def __init__(self, occurrence, view):
        """Creates and calculates render information"""

        self.event = event = occurrence.original
        self.view = view
        
        # Check permissions
        # We must check the permission in the right context.
        # This means that for multiple attendees, we must check the permission
        # in all calendar of all the attendees we have. We can shortcut though,
        # and only check those attendees that we are displaying and that are
        # attendees of the event as well.
        calendar = view.context.getCalendar()
        cal_attendees = [x.getAttendeeId() for x in calendar.getAttendees()]
        event_attendees = event.getAttendeeIds()
        asrc = zapi.getUtility(IZopeAttendeeSource, context=self.view.context)
        current_attendee = asrc.getCurrentUserAttendee()
        if current_attendee is None:
            current_attendee_id = None
        else:
            current_attendee_id = current_attendee.getAttendeeId()
            
        allowed = 0
        for attendee_id in cal_attendees:
            if attendee_id not in event_attendees:
                continue
            calendar = asrc.getMainCalendarForAttendeeId(attendee_id)
            # An attendee that has no home calendar is assumed to have no
            # real privacy.
            if ((calendar is None and (event.access == 'PUBLIC' or 
                                       attendee_id == current_attendee_id)) or 
                (calendar is not None and 
                 checkPermission('View event', event.__of__(calendar)))):
                allowed = 1
                break

        self.viewable = allowed
        # TODO: Here we could calculate short titles that fit into one row
        # and how much of the decription fits and stuff like that as well.
        if self.viewable:
            self.title = event.title_or_id()
            self.description = event.description
            self.url = view.getCalendarUrl() + '/event/'+ event.unique_id
        else:
            self.title = self.description = _('Private Event')
            self.url = ''

        event_begins = occurrence.dtstart
        event_ends = occurrence.dtstart + occurrence.duration
        self.title_and_time = "%s %02d:%02d - %02d:%02d" % (self.title, 
                                        event_begins.hour,event_begins.minute, 
                                        event_ends.hour, event_ends.minute)


class PositionedEventDisplay(EventDisplay):
    
    def __init__(self, occurrence, view):
        """Creates and calculates render information, like dimensions etc.

        View must be a IPositionedView.
        """
        EventDisplay.__init__(self, occurrence, view)
                              
        event_begins = occurrence.dtstart
        event_ends = occurrence.dtstart + occurrence.duration
        
        first_day = view.first_day
        if isinstance(first_day, datetime):
            first_day = first_day.date()
            
        if view.from_hour != 0:
            day_begins = datetime.combine(event_begins.date(), time(view.from_hour - 1))
        else:
            day_begins = datetime.combine(event_begins.date(), time(0))

        if view.to_hour != 24:
            day_ends = datetime.combine(event_begins.date(), time(view.to_hour + 1))
        else:
            day_ends = event_begins.date() + timedelta(1) 

        start_delta = event_begins - day_begins
        if start_delta < timedelta(0):
            start_delta = timedelta(0)
        self.startpos = start_delta

        if event_ends > day_ends:
            self.endpos = day_ends - day_begins
            if self.startpos > self.endpos:
                self.startpos = self.endpos
        else:
            end_delta = event_ends - day_begins
            if end_delta < timedelta(hours=1):
               end_delta = timedelta(hours=1)
            self.endpos = end_delta

        # Now calculate the css-dimensions
        self.top = (self.startpos.seconds * view.hour_height) / 3600
        duration = self.endpos - self.startpos
        self.height = (duration.seconds * view.hour_height) / 3600
        if self.height < 20:
            # Increase height, but not if we already hit the end of the day:
            max = (2 + view.to_hour - view.from_hour) * view.hour_height
            margin = max - self.top
            if margin < 20:
                self.top = self.top - (20 - margin)
            self.height = 20
                
        day = (event_begins.date() - first_day).days
        self.left = day * view.day_width
        self.width = view.day_width

        # Set Cell properties. These gets changed later when the Grid gets flatten()ed.
        Cell.__init__(self, self.top, 0, self.top + self.height, 1)
        
    def getCssPositionString(self):
        """Returns a properly formatted css-style position string.

        Usage in the template:
          tal:attributes="style event_render_info/getCssPositionString"
        """
        return "top:%spx;left:%0.1f%%;height:%spx;width:%.1f%%;"%(
            self.getFirstRow(), 
            self.getFirstCol()*100.0/self.view.width,
            self.getLastRow() - self.getFirstRow(), 
            (self.getLastCol() - self.getFirstCol())*100.0/self.view.width)
    
    def getCssStatusClass(self):
        """Returns a CSS class name according to the status of this event
        for the current user attendee (if there is one). Possible classes are:
            
            need-action
            accepted
            declined
            tentative
            delegated
            <empty>
            
        It is up to the actuall stylesheet to do something with this class.
        """
        event = self.event
        if len(event.getAttendeeIds()) < 2:
            # No need to display status for things that are not meetings
            return ''
        context = self.view.context
        calendar = context.getCalendar()
        attendee = calendar.getAttendees()[0]
        status = event.getParticipationStatus(attendee)
        if status is None:
            return ''
        return status.lower()
        
    def getCssEventClass(self):
        """Returns the type of event for CSS selection
        
        Possible types are:
            public
            private
            confidential
            meeting
            unauthorized
        """
        if not self.viewable:
            return 'unauthorized'
        if len(self.event.getAttendeeIds()) > 1:
            return 'meeting'
        return self.event.access.lower()
