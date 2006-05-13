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
from calcore import cal
from datetime import datetime
from Products.CalZope.browser.week import WeekView
from AccessControl import getSecurityManager
from calcore.interfaces import IAttendeeSource, IStorageManager
from zope.app import zapi

class CalendarEditView:
    """View to edit the calendar"""
    
    def update(self):
        request = self.request
        context = self.context
        form = request.form

        self.title = (form.has_key('title') and form['title'] 
                      or context.title)
        self.description = (form.has_key('description') and form['description'] 
                            or context.description)
        self.attendee_type = (form.has_key('attendee_type') and 
                              form['attendee_type'] or 
                              getattr(context, '_attendee_type', ''))

        # Set up the possible attendee_types in the select-box
        if self.attendee_type == 'INDIVIDUAL':
            self.attendee_types = ['INDIVIDUAL']
        else:
            asrc = zapi.getUtility(IAttendeeSource, context=context)
            self.attendee_types = asrc.getAttendeeTypes()
            if 'INDIVIDUAL' in self.attendee_types:
                self.attendee_types.remove('INDIVIDUAL')

        if 'SUBMIT_EDIT' in form:
            changed = 0
            if form['title'] != context.title:
                context.title = form['title']
                changed = 1
            if form['description'] != context.description:
                context.description = form['description']
                changed = 1
            a_type = form.get('attendee_type')
            if  a_type is not None and a_type != context._attendee_type:
                context._attendee_type = a_type
                changed = 1

            if changed:
                self.request.form['portal_status_message'] = 'psm_content_changed'
        
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
            for key in form.keys():
                if not key.startswith('remove_'):
                    continue
                attendee = attendee_source.getAttendee(key[len('remove_'):])
                self.context.removeAttendee(attendee)
        elif 'UPDATE_ADD' in form:
            attendee_source = self._getAttendeeSource()
            for key in form.keys():
                if not key.startswith('add_'):
                    continue
                attendee = attendee_source.getAttendee(key[len('add_'):])
                self.context.addAttendee(attendee)

    def _getAttendeeSource(self):
        return zapi.getUtility(IAttendeeSource, context=self.context)


    def getSearchResults(self):
        attendee_source = self._getAttendeeSource()
        if self.use_query == '':
            return []
        result = attendee_source.findByName(self.use_query)
        # Filter out the ones that exist already
        attendeelist = [x.getAttendeeId() for x in self.context.getAttendees()]
        res =  []
        for attendee in result:
            id = attendee.getAttendeeId()
            cal = attendee_source.getMainCalendarForAttendeeId(id)
            # Check that you have view permission (or no calendar exists)
            if (cal is not None and
                not self.checkPermission('View calendar', cal)):
                continue
            # Filter out the ones that exist already
            if id in attendeelist:
                continue
            res.append(attendee)
        return res

    def checkPermission(self, permission, object=None):
        if object is None: # Default to the event
            object = self.context
        user = getSecurityManager().getUser()
        return user.has_permission(permission, object)


class CalendarView(BrowserView, WeekView):
    def getNeedsActionAmount(self):
        """Get all events that need action for attendees.
        """
        calendar = self.context.getCalendar()
        return len(getNeedsActionEvents(calendar))

    def getAttendedAmount(self):
        return len(getAttendedEvents(self.context.getCalendar()))
    
    def getOrganizedAmount(self):
        """Get all events in the future that attendees organized.
        """
        calendar = self.context.getCalendar()
        return len(getOrganizedEvents(calendar))
    
    def getWeekUrl(self):
        today = datetime.today()
        year = today.year
        weeknr = today.isocalendar()[1]
        return '%s/week/%s/%s' % (self.context.absolute_url(), year, weeknr)
        
    def displayEventLists(self):
        if not self.checkPermission('Manage participation status'):
            return 0
        return (self.getNeedsActionAmount() or
                self.getAttendedAmount() or
                self.getOrganizedAmount()) != 0

class GotoCalendarView(BrowserView):
    
    def __call__(self):
        calendar = self.context.getCalendar()
        url = calendar.absolute_url()
        response = self.request.RESPONSE
        response.redirect(url)
    
class EventsView(BrowserView):
    def _getEvents(self):
        raise NotImplementedError

    def getEvents(self):
        events = self._getEvents()
        events.sort(lambda x, y: cmp(x.dtstart, y.dtstart))
        events = [event.__of__(self.context) for event in events]
        return events

    def getParticipationStatus(self, event):
        attendee = zapi.getUtility(IAttendeeSource, context=self
                                   ).getCurrentUserAttendee()
        return event.getParticipationStatus(attendee)
        
class NeedsActionEventsView(EventsView):
    def updateParticipationStatus(self):
        if not self.request.has_key('update_participation_status'):
            return
        participation_status = self.request['participation_status']
        event_ids = self.request.get('event_ids')
        if event_ids is None:
            # XXX Should set a psm_ message here.
            return
        calendar = self.context.getCalendar()
        attendee = zapi.getUtility(IAttendeeSource, context=self.context
                                   ).getCurrentUserAttendee()
        for event_id in event_ids:
            event = calendar.getEvent(event_id)
            event.setParticipationStatus(attendee, participation_status)

    def _getEvents(self):
        return getNeedsActionEvents(self.context.getCalendar())

class AttendedEventsView(NeedsActionEventsView):
    def _getEvents(self):
        return getAttendedEvents(self.context.getCalendar())
    
class OrganizedEventsView(EventsView):
    def _getEvents(self):
        return getOrganizedEvents(self.context.getCalendar())
    
def getNeedsActionEvents(calendar):
    """Get all the events in the future that need action.
    """
    return calendar.getEvents(
        (datetime.now(), None),
        cal.SearchCriteria(participation_status='NEEDS-ACTION'))

def getAttendedEvents(calendar):
    return calendar.getEvents(
        (datetime.now(), None),
        cal.SearchCriteria(participation_status='ACCEPTED'))

def getOrganizedEvents(calendar):
    """Get all events in the future that attendees of calendar organized.
    """
    period = (datetime.now(), None)
    events = []
    for attendee in calendar.getAttendees():
        events.extend(
            attendee.getEvents(
            period,
            cal.SearchCriteria(organizer=attendee)))
    return events

    
