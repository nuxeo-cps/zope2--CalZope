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

from calcore import cal, isoweek
from calcore.interfaces import IAttendeeSource, IStorageManager, \
     IEventModifiedEvent

# python
from datetime import datetime
import calendar, icalendar

# zope
from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder
from ZODB.PersistentMapping import PersistentMapping
from AccessControl import ClassSecurityInfo, getSecurityManager
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

import helpers
import storage
from interfaces import IYear, IMonth, IDay
from interfaces import IEventList, IWeekList, IWeekYear, IWeek
from interfaces import IZopeAttendeeSource, IBusyChecker,IZopeStorageManager
from zope.interface import implements
from zope.app import zapi
from Products.Five.traversable import  FiveTraversable

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")

class CalendarTool(Folder):
    # Deprecated, but needs to stay for upgrade. Can be removed only when we
    # decide that upgrade directly from 1.x isn't supported anymore.

    meta_type = 'Calendar Tool'

InitializeClass(CalendarTool)

def manage_addCalendarTool(context, REQUEST=None):
    """Add a calendar tool"""
    id = 'portal_calendar'
    obj = CalendarTool(id)
    destination = getattr(context, 'Destination', None)
    if destination:
        context = destination()
    context._setObject(id, obj)
    obj = context[id]
    manage_addStorageManager(obj, 'storage_manager', '')
    manage_addUserFolderAttendeeSource(obj, 'attendee_source', '')
    helpers.add_and_edit(context, id, REQUEST)
    return ''

class StorageManager(SimpleItem, cal.StorageManagerBase):
    security = ClassSecurityInfo()

    implements(IZopeStorageManager)
    
    meta_type = 'Calendar Storage Manager'

    def __init__(self, id='IStorageManager', title=''):
        StorageManager.inheritedAttribute('__init__')(self)
        self.id = id
        self.title = title
        # simple ZODB storage hardcoded in for now
        self.setStorage(storage.ZODBStorage('storage'))

    def createEvent(self, unique_id=None, **kw):
        return self._storage.createEvent(unique_id,
                                         storage.ZopeEventSpecification(**kw))

    def notifyEventEvent(self, event):
        # On event modification, reindex event:
        if IEventModifiedEvent.providedBy(event):
            self._storage.reindexEvent(event.event.unique_id, event.event)
        # (Reindex on adding and deleting is handled elsewhere).
    
    
InitializeClass(StorageManager)

manage_addStorageManagerForm = PageTemplateFile(
    "www/storageManagerAdd", globals(),
    __name__='manage_addStorageManagerForm')

def manage_addStorageManager(context, id, title, REQUEST=None):
    """Add a calendar storage manager"""
    obj = StorageManager(id, title)
    context._setObject(id, obj)
    helpers.add_and_edit(context, id, REQUEST)
    return ''

class UserFolderAttendeeSource(SimpleItem):
    """A very simplistic attendee source, designed to be replaced.
    """
    security = ClassSecurityInfo()

    meta_type = 'Calendar Attendee Source (User Folder)'

    implements(IZopeAttendeeSource)

    def __init__(self, id='IAttendeeSource', title=''):
        self.id = id
        self.title = title

    def getMainCalendarForAttendeeId(self, attendee_id):
        # This should be overridden in more advance portal implementations.
        # This implementation knows nothing about home calendars for
        # individuals and it only knows about individuals. So there ya go.
        return None

    def getAttendeeTypes(self):
        return ['INDIVIDUAL']

    def getAttendee(self, attendee_id):
        # XXX no checking yet whether user exists at all
        attendee = Attendee(attendee_id, attendee_id, 'INDIVIDUAL')
        homecal = self.getMainCalendarForAttendeeId(attendee_id)
        if homecal is None:
            return attendee.__of__(self)
        # This is to acquire the security settings from the calendar:
        return attendee.__of__(homecal)

    def getCurrentUserAttendee(self):
        return self.getAttendee(getSecurityManager().getUser().getId())

    def findByName(self, query_str, attendee_type=None):
        # don't deal with anything but individuals
        if attendee_type is not None and attendee_type != 'INDIVIDUAL':
            return []
        result = []
        for userid in self.get_valid_userids():
            if query_str not in userid:
                continue
            result.append(self.getAttendee(userid))
        return result

    def getAttendeesOfType(self, attendee_type):
        result = []
        if attendee_type != 'INDIVIDUAL':
            return []
        for userid in self.get_valid_userids():
            result.append(self.getAttendee(userid))
        return result

    def getAttendeeFromSpec(self, vcaladdress):
        id = vcaladdress.decode()
        return self._attendees.get(id, None)

    def notifyEventEvent(self, event):
        # I don't need to do anything in this implementation.
        pass

InitializeClass(UserFolderAttendeeSource)

manage_addUserFolderAttendeeSourceForm = PageTemplateFile(
    "www/ufAttendeeSourceAdd", globals(),
    __name__='manage_addUserFolderAttendeeSourceForm')

def manage_addUserFolderAttendeeSource(context, id, title, REQUEST=None):
    """Add a user-folder based attendee source"""
    obj = UserFolderAttendeeSource(id, title)
    context._setObject(id, obj)
    helpers.add_and_edit(context, id, REQUEST)
    return ''

class Attendee(SimpleItem, cal.AttendeeBase):
    security = ClassSecurityInfo()

    meta_type = 'Calendar Attendee'

    def __init__(self, attendee_id, name, attendee_type):
        Attendee.inheritedAttribute('__init__')(
            self, attendee_id, name, attendee_type)
        self.id = attendee_id
        self.title = name

    def _getStorageManager(self):
        #return self.portal_calendar.storage_manager
        return zapi.getUtility(IStorageManager, context=self)

    def getUserId(self):
        return self.id

InitializeClass(Attendee)

class Calendar(SimpleItem, cal.CalendarBase):
    security = ClassSecurityInfo()

    meta_type = 'Calendar'

    def __init__(self, id, title='', description=''):
        Calendar.inheritedAttribute('__init__')(self)
        self.id = id
        self.title = title
        self.description = description

    def _initAttendees(self):
        return PersistentMapping()

    # purely used for acquisition
    def getCalendar(self):
        return self.aq_inner

    # getting attendees in right acquisition context, is needed
    # as attendee tries to do _getCalendar which is implemented using
    # acquisition
    def getAttendees(self):
        result = []
        for attendee in Calendar.inheritedAttribute('getAttendees')(self):
            result.append(attendee.__of__(self))
        return result

    def getWeekNr(self):
        return datetime.today().isocalendar()[1]

    def getYear(self):
        return datetime.today().year

    def _getStorageManager(self):
        return zapi.getUtility(IStorageManager, context=self)

    def _getAttendeeSource(self):
        return zapi.getUtility(IAttendeeSource, context=self)

    def export(self, period=(None, None), search_criteria=None):
        """Export calendar data in ICalendar format.

        Only event organized on this calendar are exported (no those from other
        calendars registered thanks to the multi view feature).

        Private events' content (title, description, location, ...) is hidden but
        the event dates are always exported.
        """
        ical = icalendar.Calendar()
        ical.add('prodid', '-//CPS Shared Calendar//nuxeo.com//')
        ical.add('version', '1.0')

        security = getSecurityManager()
        for event in self.getEvents(period, search_criteria):
            # do not export events that comes from other calendars (multi
            # view feature) that conflicts with the ability of ical clients to
            # subscribe directly to other calendars)
            if self.getMainAttendee().getAttendeeId() != event.getOrganizerId():
                continue

            # hide the content of private event
            private = not security.checkPermission('View event',
                                                   event.__of__(self))
            e = event.export(private)
            ical.add_component(e)
        ical_text = ical.as_string()
        self._logger.debug('export generated ical text: \n\n%s\n\n' % ical_text)
        return ical_text

    def _importNewEvent(self, uid, e):
        """Import new event only if permission ok"""
        security = getSecurityManager()
        if security.checkPermission('Create events', self):
            cal.CalendarBase._importNewEvent(self, uid, e)

    def _importExistingEvent(self, uid, e):
        """Update event if permission ok"""
        event = self.getEvent(uid)
        security = getSecurityManager()
        if security.checkPermission('Modify event', event.__of__(self)):
            cal.CalendarBase._importExistingEvent(self, uid, e)

    def _deleteEvent(self, event):
        """Delete only if permission ok

        This overrides CalendarBase._deleteEvent method that is only used at
        ical import time.
        """
        security = getSecurityManager()
        if security.checkPermission('Delete event', event.__of__(self)):
            cal.CalendarBase._deleteEvent(self, event)


class CalendarTraversable(FiveTraversable):

    # url space

    # day: calendar/2005/05/30
    # month: calendar/2005/05
    # year: calendar/2005
    # week: calendar/week/2005/3
    # weekday: calendar/week/2005/3/2
    # event: calendar/event/1223

    def traverse(self, name, furtherPath):
        if name == 'event':
            return EventList().__of__(self._subject)
        elif name == 'week':
            return WeekList().__of__(self._subject)
        else:
            try:
                year = int(name)
                return Year(year).__of__(self._subject)
            except ValueError:
                pass
        if name == 'getId':
            # XXX Special hack I don't understand.
            # Maybe I can get rid of it now when I use Traversal adapters?
            return getattr(self._subject, name)

        return FiveTraversable.traverse(self, name, furtherPath)


InitializeClass(Calendar)

manage_addCalendarForm = PageTemplateFile(
    "www/calendarAdd", globals(),
    __name__='manage_addCalendarForm')

def manage_addCalendar(context, id, title, REQUEST=None):
    """Add a calendar."""
    obj = Calendar(id, title)
    context._setObject(id, obj)
    helpers.add_and_edit(context, id, REQUEST)
    return ''

class Year(SimpleItem):
    security = ClassSecurityInfo()

    meta_type = 'Calendar Year'

    implements(IYear)

    def __init__(self, year):
        self.id = str(year)
        self.title = self.id
        self._year = year

    def getYear(self):
        return self._year

    def getMonths(self):
        return range(1, 13)

class YearTraversable(FiveTraversable):

    def traverse(self, name, furtherPath):
        try:
            month = int(name)
            return Month(self._subject._year, month).__of__(self._subject)
        except ValueError:
            pass
        return FiveTraversable.traverse(self, name, furtherPath)


InitializeClass(Year)

class Month(SimpleItem):
    security = ClassSecurityInfo()

    meta_type = 'Calendar Month'

    implements(IMonth)

    def __init__(self, year, month):
        self.id = str(month)
        self.title = _('calendar_month_%s' % self.id)
        self._year = year
        self._month = month

    def getYear(self):
        return self._year

    def getMonth(self):
        return self._month

    def getDays(self):
        weekday, amount_days = calendar.monthrange(self._year, self._month)
        return range(1, amount_days + 1)

    def getDateForDay(self, day):
        return datetime(self._year, self._month, day)

class MonthTraversable(FiveTraversable):

    def traverse(self, name, furtherPath):
        try:
            day = int(name)
            return Day(self._subject._year, self._subject._month, day).__of__(self._subject)
        except ValueError:
            pass
        return FiveTraversable.traverse(self, name, furtherPath)

InitializeClass(Month)

class Day(SimpleItem):
    security = ClassSecurityInfo()

    meta_type = 'Calendar Day'

    implements(IDay)

    def __init__(self, year, month, day):
        self.id = str(day)
        self.title = self.id
        self._year = year
        self._month = month
        self._day = day

    def getYear(self):
        return self._year

    def getMonth(self):
        return self._month

    def getDay(self):
        return self._day

InitializeClass(Day)

class EventList(SimpleItem):
    security = ClassSecurityInfo()

    meta_type = 'Calendar Event List'

    implements(IEventList)

    def __init__(self):
        self.id = 'event'
        self.title = _(self.id)

    def Title(self):
        return self.title


class EventListTraversable(FiveTraversable):

    def traverse(self, name, furtherPath):
        try:
            calendar = self._subject.getCalendar()
            event = calendar.getCalendar().getEvent(name)
            c_attendees = calendar.getAttendees()
            e_attendees = event.getAttendeeIds()
            for attendee in c_attendees:
                if attendee.getAttendeeId() in e_attendees:
                    return event.__of__(self._subject)
            # None of this calendars attendees are attendees on the event.
            # The event should not be displayed:
            raise AttributeError
        except (ValueError, KeyError):
            pass
        return FiveTraversable.traverse(self, name, furtherPath)

InitializeClass(EventList)

class WeekList(SimpleItem):
    security = ClassSecurityInfo()

    meta_type = 'Calendar Week List'

    implements(IWeekList)

    def __init__(self):
        self.id = 'week'
        self.title = _(self.id)

    def Title(self):
        """Return a translated title for the breadcrumb"""
        return self.title


class WeekListTraversable(FiveTraversable):

    def traverse(self, name, furtherPath):
        try:
            year = int(name)
            return WeekYear(year).__of__(self._subject)
        except ValueError:
            pass
        return FiveTraversable.traverse(self, name, furtherPath)

InitializeClass(WeekList)

class WeekYear(SimpleItem):
    meta_type = 'Calendar Week Year'

    implements(IWeekYear)

    def __init__(self, year):
        self.id = str(year)
        self.title = self.id
        self._year = year

    def getYear(self):
        return self._year

    def getWeeks(self):
        return range(1, isoweek.getWeeksInYear(self._year) + 1)

class WeekYearTraversable(FiveTraversable):

    def traverse(self, name, furtherPath):
        try:
            week_nr = int(name)
            return Week(self._subject._year, week_nr).__of__(self._subject)
        except ValueError:
            pass
        return FiveTraversable.traverse(self, name, furtherPath)

InitializeClass(WeekYear)

class Week(SimpleItem):
    security = ClassSecurityInfo()

    meta_type = 'Calendar Week'

    implements(IWeek)

    def __init__(self, year, week_nr):
        self.id = str(week_nr)
        self.title = _("Week ${week}", mapping={'week': self.id})
        self._year = year
        self._week_nr = week_nr

    def getYear(self):
        return self._year

    def getWeekNr(self):
        return self._week_nr

    def getDateForWeekday(self, weekday):
        return isoweek.weeknr2datetime(self._year, self._week_nr, weekday)

class WeekTraversable(FiveTraversable):

    def traverse(self, name, furtherPath):
        try:
            d = self._subject.getDateForWeekday(int(name))
            return Day(d.year, d.month, d.day).__of__(self._subject)
        except ValueError:
            pass
        return FiveTraversable.traverse(self, name, furtherPath)

InitializeClass(Week)

from zope.schema.interfaces import ValidationError
from zope.i18n import translate

class BusyUsersError(ValidationError):

    def __init__(self, users):
        self.users = ', '.join(users)

    def doc(self):
        return translate(_("Some attendees are busy during the selected period: ${users}",
                mapping={'users': self.users}))

class BusyUserError(ValidationError):
    __doc__ = "This attendee is busy during the selected period"


class BaseBusyChecker(object):

    implements(IBusyChecker)
    def _isManager(self, calendar):
        user = getSecurityManager().getUser()
        return user.has_permission('Manage participation status', calendar)

    def check(self, dtstart, dtend):
        from calcore.cal import SearchCriteria
        storage = zapi.getUtility(IStorageManager, context=self.context)
        asrc = zapi.getUtility(IZopeAttendeeSource, context=self.context)
        currentattendee = asrc.getCurrentUserAttendee().getAttendeeId()
        attendees = [asrc.getAttendee(a) for a in self.attendees]

        sc = SearchCriteria(attendees=attendees)
        events = storage.getEvents((dtstart, dtend), sc)
        busy = []
        for event in events:
            if (event.status != 'CONFIRMED' or event.transparent or
                event.getId() in self.ignore_events):
                continue
            busy.extend(event.getAttendeeIds(participation_status='ACCEPTED'))

        users = []
        for attendeeid in busy:
            maincal = asrc.getMainCalendarForAttendeeId(attendeeid)
            # You are trying to double book yourself. You probably don't
            # want that:
            if attendeeid == currentattendee:
                raise BusyUserError()
            if self._isManager(maincal):
                # I'm manager for this attendee and allowed to double book.
                continue
            else:
                # XXX I just realized we have no consistent and defined API
                # for attendees titles. That should be fixed.
                title = asrc.getAttendee(attendeeid).title
                if title not in users:
                    users.append(title)
        if users:
            raise BusyUsersError(users)

        # All is well
        return

class AddBusyChecker(BaseBusyChecker):
    """A busy checker for add-views"""

    def __init__(self, addview):
        self.context = addview.context
        session = addview.request.get('SESSION', {})
        attendees = session.get('meeting_helper_attendees', [])
        if attendees:
            self.attendees = attendees
        else:
            calendar = addview.context.getCalendar()
            self.attendees = [calendar.getMainAttendee().getAttendeeId()]
        if getattr(addview, '_event_unique_id', None) is not None:
            self.ignore_events = [addview._event_unique_id]
        else:
            self.ignore_events = []

class EventBusyChecker(BaseBusyChecker):
    """A busy checker for events"""
    def __init__(self, event):
        self.context = event
        self.attendees = event.getAttendeeIds()
        self.ignore_events = [event.getId()]

class AttendeeBusyChecker(BaseBusyChecker):
    """A busy checker for attendees"""
    def __init__(self, attendee):
        self.context = attendee
        self.attendees = [attendee.getAttendeeId()]
        self.ignore_events = []

# Event support

def handleEventEvent(event):
    # Call both the storage manager and attendee source here.
    # The attendee source doesn't actually care about events, 
    # but might want to care in the future.
    
    # BBB We should really look for IZopeStorageManager here, but to keep
    # Five 1.3 compatibility, we look for IStorageManager. This will
    # fixed when we drop Zope 2.9 support.
    storage = zapi.getUtility(IStorageManager)
    storage.notifyEventEvent(event)
    att_src = zapi.getUtility(IZopeAttendeeSource)
    att_src.notifyEventEvent(event)
