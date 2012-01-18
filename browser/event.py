# -*- coding: iso-8859-15 -*-
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
  event.py
  
  Keeps the views used for differen event editing forms.
"""
from datetime import timedelta
from AccessControl import Unauthorized
from AccessControl import getSecurityManager

from Products.Five import BrowserView
from Products.Five.form import EditView

from zope.component import getView
from zope.interface import Interface
from zope.schema import Choice, Set
from zope.schema import getFieldNamesInOrder
from zope.app.location.interfaces import ILocation
from zope.app.location import LocationProxy
from zope.app.form.utility import setUpEditWidgets, applyWidgetsChanges
from zope.app import zapi
from zope.event import notify

from calcore.interfaces import IDailyRecurrenceRule, IWeeklyRecurrenceRule, \
     IMonthlyRecurrenceRule, IYearlyRecurrenceRule, IStorageManager
from calcore.events import EventModifiedEvent
from calcore.recurrent import DailyRecurrenceRule, WeeklyRecurrenceRule, \
     MonthlyRecurrenceRule, YearlyRecurrenceRule

from Products.CalZope.interfaces import IZopeAttendeeSource
from Products.CalZope.interfaces import IBusyChecker
from Products.CalZope.zopecal import BusyUserError, BusyUsersError

from zope.i18n import translate
from zope.i18nmessageid import MessageFactory

from Products.CalZope.browser.utils import LinkProtectable

_ = MessageFactory("calendar")

class IRecurrenceSelectorSchema(Interface):
    recurrence_type = Choice(
        title=_("Recurrence type"),
        vocabulary="RecurrenceVocabulary",
        description=_("Selects the recurrence rule for the object"))
 
class IWeeklyRecurrenceRuleFix(IWeeklyRecurrenceRule):
    
    weekdays = Set(
        title=_("Weekdays"),
        value_type=Choice(title=_("Weekday"),
                          vocabulary="CalendarWeekdays"),
        description=_("""
        A set of weekdays when this event occurs.

        Weekdays are represented as integers from 0 (Monday) to 6 (Sunday).
        This is what the `calendar` and `datetime` modules use.

        The event repeats on the weekday of the first occurence even
        if that weekday is not in this set.
        """))
     
from calcore.cal import CalendarVocabularyFactory

def RecurrenceVocabulary(context):
    return CalendarVocabularyFactory((
        'No recurrence', 
        'Daily recurrence', 
        'Weekly recurrence',
        'Monthly recurrence', 
        'Yearly recurrence',
        ))

# A quick hack before we make a registry + vocabulary out of this:
recurrence_rules = {'No recurrence': None,
                    'Daily recurrence': DailyRecurrenceRule,
                    'Weekly recurrence': WeeklyRecurrenceRule,
                    'Monthly recurrence': MonthlyRecurrenceRule, 
                    'Yearly recurrence': YearlyRecurrenceRule}

recurrence_names = {None: 'No recurrence',
                    IDailyRecurrenceRule: 'Daily recurrence',
                    IWeeklyRecurrenceRule: 'Weekly recurrence',
                    IMonthlyRecurrenceRule: 'Monthly recurrence',
                    IYearlyRecurrenceRule: 'Yearly recurrence'}

class YearlyRecurrenceRuleView:

    # Every year
    # Every year, for 3 years
    # Every year, until [date]
    # Every 2 years
    # Every 2 years, for 6 years
    # Every 2 years, until [date]
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.interval = context.interval
        
        self.count = context.count
        self.until = context.until

        self.unit = 'year'
    
    def __call__(self):
        recurrence = []
        interval = self.interval
        if interval > 1:
            recurrence.append('Every %s %ss' % (interval, self.unit))
        else:
            recurrence.append('Every %s' % self.unit)
            
        count = self.count
        if count:
            recurrence.append('for %s times' % count)
            
        until = self.until
        if until:
            recurrence.append('until %s' % until.strftime(
                str(self.xlate('%Y-%m-%d'))))

        return ', '.join(recurrence)

class MonthlyRecurrenceRuleView(YearlyRecurrenceRuleView):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.interval = context.interval
        self.count = context.count
        self.until = context.until
        
        self.unit = 'month'

class DailyRecurrenceRuleView(YearlyRecurrenceRuleView):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.interval = context.interval
        self.count = context.count
        self.until = context.until
        
        # Hack to show a week per 7 days.
        if self.interval % 7:
            self.unit = 'day'
        else:
            self.interval = self.interval / 7
            self.unit = 'week'

class WeeklyRecurrenceRuleView(YearlyRecurrenceRuleView):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.interval = context.interval
        self.count = context.count
        self.until = context.until
        
        self.unit = 'week'

class EventView(BrowserView, LinkProtectable):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.protect_links_javascript=context.getCalendar().areLinksProtected()
        
        self.document_url = str(getattr(self.context, 'document', ''))
        if self.document_url:
            try:
                doc = self.context.unrestrictedTraverse(self.document_url, None)
            except AttributeError: 
                # Happens when the view is called for an event without a context.
                doc = None
            if doc is not None and getattr(doc, 'title_or_id', None):
                self.document_title = doc.title_or_id()
            else:
                self.document_title = self.context.document
        else:
            self.document_title  = ''

    def checkDelete(self):
        if self.request.form.has_key('SUBMIT_CANCEL'):
            url = self.context.absolute_url()
            self.request.RESPONSE.redirect(url)
        elif self.request.form.has_key('SUBMIT_DELETE'):
            self.delete()
            return
    
    def xlate(self, str):
        return translate(_(str),context=self.request)

    def starttime(self):
        start = self.context.dtstart
        return start.strftime(str(self.xlate('%Y-%m-%d')) + ' %H:%M')

    def startdate(self):
        start = self.context.dtstart
        return start.strftime(str(self.xlate('%Y-%m-%d')))

    def endtime(self):
        start = self.context.dtstart
        duration = self.context.duration
        end = start + duration
        return end.strftime(str(self.xlate('%Y-%m-%d')) + ' %H:%M')

    def enddate(self):
        start = self.context.dtstart
        duration = self.context.duration
        end = start + duration
        if self.allday():
            # If it is an all day event, the end datetime is until 00:00h
            # of the following day. This makes a somewhat confusing display
            # of the dates. So, in that case substract one day from the
            # end date.
            end = end - timedelta(days=1)
        return end.strftime(str(self.xlate('%Y-%m-%d')))
    
    def duration(self):
        if self.allday():
            duration = self.context.duration - timedelta(days=1)
            duration = str(duration)
            return duration.split(',')[0]
        else:
            duration = self.context.duration
            return str(duration)[:-3]

    def allday(self):
        return self.context.allday
    
    def getDayUrl(self):
        import pdb;pdb.set_trace()
        dt = self.context.dtstart
        base = self.context.getCalendar().absolute_url()
        return '%s/%s/%s/%s' % (base, dt.year, dt.month, dt.day)

    def getWeekUrl(self):
        dt = self.context.dtstart
        base = self.context.getCalendar().absolute_url()
        return '%s/week/%s/%s' % (base, dt.year, dt.isocalendar()[1])

    def getMonthUrl(self):
        dt = self.context.dtstart
        base = self.context.getCalendar().absolute_url()
        return '%s/%s/%s' % (base, dt.year, dt.month)
    
    def recurrence(self):
        return self.getRecurrenceRule()()
    
    def recurUntilStr(self):
        recur = self.getRecurrenceRule()
        if recur is None:
            return ''
        return recur.until.strftime(str(self.xlate('%Y-%m-%d')))
    
    def getRecurrenceRule(self):
        request = self.request
        recurrence = self.context.recurrence
        if recurrence is None:
            return None
        recurrenceruleview = getView(recurrence, 'recurrencerule', request)        
        return recurrenceruleview
    
    def delete(self):
        week_url = self.getWeekUrl()
        s = zapi.getUtility(IStorageManager, context=self.context)
        s.deleteEvent(self.context)
        response = self.request.RESPONSE
        response.redirect(week_url)

    def getOrganizerTitle(self):
        organizer = self.context.getOrganizerId()
        asrc = zapi.getUtility(IZopeAttendeeSource, context=self.context)
        organizer = asrc.getAttendee(organizer)
        return organizer.title
    
    def url(self):
        calendar = self.context.getCalendar()
        calurl = calendar.absolute_url()
        return calurl + '/event/' + self.context.unique_id
        

    
class AttendeeManagementView(BrowserView):
    """A view for events with helper functions for attendee management"""
    
    use_query = ''
    
    def update(self):
        form = self.request.form
        
        # First fetch the search query:
        if 'UPDATE_SEARCH' in form: # New search performed
            self.use_query = form['search_query']
        elif 'use_query' in form: # No new search, but an old one.
            self.use_query = form['use_query']
        
        # Do any actions
        if 'UPDATE_REMOVE' in form:
            removes = [key for key in form.keys() if key.startswith('remove_')]
            self.removeAttendees(removes)
        elif 'UPDATE_ADD' in form:
            adds = [key for key in form.keys() if key.startswith('add_')]
            self.inviteAttendees(adds)
        elif 'UPDATE_STATUS' in form:
            updates = [key for key in form.keys() if key.startswith('new_status_')]
            self.updateStatus(updates)

    def removeAttendees(self, removes):
        if not self.canManageAttendees():
            raise Unauthorized('You do not have the permission to remove ' \
                               'attendees from this event')
        attendee_source = self._getAttendeeSource()
        for id in removes:
            id = id[len('remove_'):]
            attendee = attendee_source.getAttendee(id)
            self.context.setParticipationStatus(attendee, None)

    def inviteAttendees(self, adds):
        attendee_source = self._getAttendeeSource()
        attendees = []
        for id in adds:
            id = id[len('add_'):]
            attendee = attendee_source.getAttendee(id)
            attendees.append(attendee)
            
        self.context.invite(attendees)

    def updateStatus(self, statuses):
        #ctool = self._getCalendarTool()
        attendee_source = self._getAttendeeSource()
        for attendee_id in statuses:
            id = attendee_id[len('new_status_'):]
            attendee = attendee_source.getAttendee(id)
            if not self.canChangeAttendeeStatus(attendee):
                raise Unauthorized('You do not have the permission to change ' \
                      'the attendee status for attendee %s' % attendee.title)
            self.context.setParticipationStatus(attendee, 
                                                self.request.form[attendee_id])

    def getSearchResults(self):
        attendee_source = self._getAttendeeSource()
        attendees = attendee_source.findByName(self.use_query)
        dtstart = self.context.dtstart
        dtend = dtstart + self.context.duration
        results = []
        current_attendees = self.context.getAttendeeIds()
        for attendee in attendees:
            if attendee.getAttendeeId() in current_attendees:
                continue
            checker = IBusyChecker(attendee)
            try:
                checker.check(dtstart, dtend)
                busy = False
            except (BusyUserError, BusyUsersError):
                busy = True
            results.append((attendee, busy))
            
        return results
        
    
    def _getAttendeeSource(self):
        return zapi.getUtility(IZopeAttendeeSource)
        
    def getAttendees(self):
        return [self._getAttendeeSource().getAttendee(id) for id in self.context.getAttendeeIds()]

    def validStatusList(self, attendee):
        """Returns a list of those statuses the attendee can get changed into"""
        #ctool = self._getCalendarTool()
        if not self.canChangeAttendeeStatus(attendee):
            # You don't have the right to change this attendees status
            return []
        list = ['ACCEPTED', 'DECLINED', 'TENTATIVE', 'DELEGATED']
        current_status = self.context.getParticipationStatus(attendee)
        if not current_status in list:
            list.append(current_status)
        return list

    def canManageAttendees(self):
        return self.checkPermission('Manage attendees')

    def canChangeAttendeeStatus(self, attendee):
        #ctool = self._getCalendarTool()
        return self.canManageAttendees() or self.checkPermission(
            'Manage participation status', attendee)
        
    def checkPermission(self, permission, object=None):
        if object is None: # Default to the event
            object = self.context
        user = getSecurityManager().getUser()
        return user.has_permission(permission, object)
                
class RecurrenceView(EditView):
    """A event view that enables you to edit the recurrence rule

    Because recurrence rules are not Extentionclasses, you can't
    make them traversable, and therefore you can't have this view
    directly on the recurrence object. In Zope3 this problem
    goes away, and the recurrence rules can be directly editable."""
    fieldNames = []
    
    def __init__(self, context, request):
        EditView.__init__(self, context, request)
        self.label = "Edit recurrence"

    def changed(self):
        # Since recurrent rules are not persistent, we need to mark the
        # containing object (the event) as dirty
        self.context._p_changed = 1
        rtype = recurrence_rules[self.request.form['field.recurrence_type']]
        if rtype is None:
            if self.context.recurrence is not None:
                self.context.recurrence = None
        elif not isinstance(self.context.recurrence, rtype):
            # The recurrence type changed: Change the recurrence object too.
            # TODO: keep fields that are in the basic type
            self.context.recurrence = rtype()
        # Set up the widgets again.
        sm = zapi.getUtility(IStorageManager, context=self.context)
        notify(EventModifiedEvent(self.context))
        self._setUpWidgets()

    def _setUpWidgets(self):
        # This is possibly a bit to clever for our own good, but it seems to
        # work well. An alternative is to use adapters between the recurrence
        # rules and an an interface that has recurrence_type.
        # Or, possibly it could work to have a display that has a 
        # recurrence_type field and a recurrence field, and use a subform
        # with the ObjectWidget...
        
        adapted = self.context.recurrence
        if adapted is None:
            self.schema = IRecurrenceSelectorSchema
            adapted = self
            adapted.recurrence_type = recurrence_names[None]
        else:
            for schema in recurrence_names.keys():
                if schema is not None and schema.providedBy(adapted):
                    break
            self.context.recurrence.recurrence_type = recurrence_names[schema]
            class IThisSchema(IRecurrenceSelectorSchema, schema):
                pass
            self.schema = IThisSchema
            
        self.adapted = adapted
        if not ILocation.providedBy(adapted):
            adapted = LocationProxy(adapted)
        adapted.__parent__ = self.context
        
        fieldNames = getFieldNamesInOrder(self.schema)
        fieldNames.remove('recurrence_type')
        self.fieldNames = ['recurrence_type'] + fieldNames
        setUpEditWidgets(self, self.schema, source=self.adapted,
                         names=self.fieldNames)

class EventListView(BrowserView):
    
    def __call__(self):
        url = self.context.getCalendar().absolute_url()
        response = self.request.RESPONSE
        response.redirect(url)
        return
