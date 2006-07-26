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

# Simple ZODB storage for calendar

import sys, random
from sets import Set
from datetime import datetime

from ZODB.PersistentMapping import PersistentMapping
from BTrees.OOBTree import OOBTree, OOSet, intersection, union
from Globals import Persistent
from OFS.SimpleItem import SimpleItem
from Acquisition import Implicit
from AccessControl import getSecurityManager
from zope.interface import implements
from zope.app import zapi

from calcore import cal
from calcore.interfaces import (
    IAttendeeSource,
    IInvitableCalendarEvent,
    IStorageManager,
)

from interfaces import IZopeAttendeeSource


_marker = []

class ZODBStorage(SimpleItem, cal.StorageBase):

    def __init__(self, storage_id, hostname=None):
        cal.StorageBase.__init__(self, storage_id, hostname)
        self.reindexAll()

    def _initEvents(self):
        return OOBTree()

    def _eventFactory(self, event_id, spec):
        return ZODBEvent(event_id, spec)

    def reindexAll(self):
        """Clears and creats all indexes, and reindexes all events"""

        # An index maps from value to id
        self._indexes = OOBTree()
        # An unindex maps from id to value
        self._unindexes = OOBTree()

        self._indexes['dtend'] = OOBTree()
        self._unindexes['dtend'] = OOBTree()
        # dtstart has only an unindex. It can be seen as a catalog "metadata"
        # field as in the catalog. It prevents the need to load many events
        # into memory when filtering on dtstart.
        self._unindexes['dtstart'] = OOBTree()

        for id, event in self._events.items():
            self.indexEvent(id, event)

    def indexEvent(self, unique_id, event):
        value = event.dtstart.utctimetuple()
        self._unindexes['dtstart'][unique_id] = value

        if event.recurrence is not None:
            if (event.recurrence.count is None and
                event.recurrence.until is None):
                # This event is open ended
                value = None
            else:
                generator = event.recurrence.apply(event)
                try:
                    while True:
                        occurrence = generator.next()
                except StopIteration:
                    pass
                start = datetime.combine(occurrence, event.dtstart.time())
                value = (start + event.duration).utctimetuple()
        else:
            value = (event.dtstart + event.duration).utctimetuple()

        row = self._indexes['dtend'].get(value, None)
        if row is None:
            row = OOSet((unique_id,))
            self._indexes['dtend'][value] = row
        else:
            row.insert(unique_id)
        self._unindexes['dtend'][unique_id] = value

    def reindexEvent(self, unique_id, event):
        self.unindexEvent(unique_id)
        self.indexEvent(unique_id, event)

    def unindexEvent(self, unique_id):
        try:
            del self._unindexes['dtstart'][unique_id]
        except KeyError:
            pass

        try:
            indexed_value = self._unindexes['dtend'][unique_id]
            index = self._indexes['dtend']
            set = index.get(indexed_value, None)
            if set is not None and unique_id in set:
                set.remove(unique_id)
                if len(set) == 0: # No need to keep empty sets.
                    del index[indexed_value]
            del self._unindexes['dtend'][unique_id]
        except KeyError:
            pass

    def createEvent(self, unique_id, spec):
        if unique_id is None:
            unique_id = cal.addrspec_unique_id('%s-%s' %
                (self._storage_id, len(self._events)), self._hostname)
        event = self._eventFactory(unique_id, spec)
        self._events[unique_id] = event
        self.indexEvent(unique_id, event)
        return event

    def deleteEvent(self, event):
        self.unindexEvent(event.unique_id)
        del self._events[event.unique_id]

    def getEvents(self, period, search_criteria):
        begin, end = period

        # Ignore those who end before the start.
        index = self._indexes['dtend']

        try:
            maxkey = index.maxKey()
        except ValueError: # No events at all
            return []
        if begin is not None:
            begin = begin.utctimetuple()
            try:
                minkey = index.minKey(begin)
                # Events that end on exactly the same same time as the
                # search period start should not be included:
                if minkey == begin:
                    excludemin = True
                else:
                    excludemin = False

                try:
                    rows = index.values(minkey, maxkey, excludemin=excludemin)
                except TypeError:
                    # XXX exclude{min|max} parameter does exist
                    # on some ZODB versions
                    if excludemin:
                        # increments minkey by one second
                        minkey = list(minkey)
                        minkey[5] += 1
                        minkey = tuple(minkey)
                    rows = index.values(minkey, maxkey)

            except ValueError:
                # No events end after start
                rows = []
        else:
            # Begin is None, so we need to search right from the start.
            # This means we must return *all* rows.
            rows = index.values()

        # The double calling of _eventValidate comes from the problem that
        # index.values() return an unmutable list. So, we can't add the
        # unbounded event row to the rows, but have to check them separately.
        # This function call slows this method with a couple of percents,
        # but I prefer that from code duplication, at least at this early
        # stage of the code, since it may change a lot still.
        if end is not None:
            end = end.utctimetuple()
        result = []
        for event_ids in rows:
            event = self._eventValidate(event_ids, end, search_criteria)
            result.extend(event)

        # Include open ended events:
        if index.has_key(None):
            events = self._eventValidate(index[None], end, search_criteria)
            result.extend(events)

        return result

    def _eventValidate(self, event_ids, end, search_criteria):
        # This method is _very_ internal, and should only be called from
        # getEvents.
        unindex = self._unindexes['dtstart']
        result = []
        for event_id in event_ids:
            try:
                dtstart = unindex[event_id]
            except KeyError:
                # In case the index contains events that no longer exist.
                continue
            if end and dtstart >= end:
                continue
            event = self._events[event_id]
            if search_criteria is not None and not search_criteria._match(event):
                continue
            result.append(event)
        return result

    def getOccurrences(self, period, search_criteria):
        cal.assertPeriodBounded(period)
        events = self.getEvents(period, search_criteria)
        result = []
        for event in events:
            result.extend(event.expand(period))
        return result


class ZopeEventSpecification(cal.EventSpecification):

    def __init__(self, dtstart, duration,
                 title='',
                 description='',
                 location='',
                 status='TENTATIVE',
                 organizer=None,
                 recurrence=None,
                 allday=False,
                 categories=None,
                 transparent=False,
                 access='PUBLIC',
                 document=''):

        cal.EventSpecification.__init__(self, dtstart, duration, title,
              description, location, status, organizer, recurrence, allday,
              categories, transparent, access)
        self.document = document


class ZODBEvent(SimpleItem, cal.EventBase):
    implements(IInvitableCalendarEvent)

    meta_type = "CalZope Event"

    def __init__(self, event_id, spec):
        cal.EventBase.__init__(self, event_id, spec)
        # zope objects need an id
        self.id = self.unique_id

    def _initParticipationState(self):
        return PersistentMapping()

    def _initParticipationRole(self):
        return PersistentMapping()

    def __ac_local_roles__(self):
        # Warning: Clever hack! This dynamically computes the roles for
        # the current user only. There is no local roles as such on these
        # objects, instead, the roles (and by extension, the permissions)
        # are defined by your attendee status and your roles on the
        # calendar through which you view the event.

        # Find the current attendee id:
        attendee_src = zapi.getUtility(IZopeAttendeeSource, context=self)
        current_attendee = attendee_src.getCurrentUserAttendee()
        current_id = current_attendee.getAttendeeId()
        attendees = [current_id]

        # Check if the current user is an attendee manager for this calendar
        current_user = getSecurityManager().getUser()
        calendar = self.getCalendar()
        roles = current_user.getRolesInContext(calendar)
        if 'AttendeeManager' in roles:
            # Current user is attendee manager for this calendars user, so
            # We'll add this calendars user to the list of current attendees
            attendees.append(calendar.getAttendees()[0].getAttendeeId())

        # Check if the current organizer is one of the relevant users, in that
        # case we should get the organizer role as well as local roles:
        if self.getOrganizerId() in attendees:
            roles.append('EventOrganizer')

        # Check through the attendees to see if they are participating:
        event_attendees = self.getAttendeeIds()
        for id in attendees:
            if id in event_attendees and 'EventParticipant' not in roles:
                roles.append('EventParticipant')

        return {current_user.getId(): list(roles)}

    def __getattr__(self, name, default=_marker):
        # View event is a "proxy permission". Nobody actually needs to
        # have that permission, instead, the name of the permission to
        # be used is returned.
        if name == '_View_event_Permission':
            if self.__dict__['access'] == 'PUBLIC':
                return '_View_public_event_Permission'
            else:
                return '_View_private_event_Permission'
        if default is _marker:
            return getattr(self.__dict__, name)
        # XXX This causes a key error instead of the standard attribute
        # errror, which is confusing. Fix that!
        return getattr(self.__dict__, name, default)

    def Title(self):
        return self.title
