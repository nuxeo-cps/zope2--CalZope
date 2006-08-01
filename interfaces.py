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

from zope.interface import Interface
from zope.schema import Text, TextLine, Datetime
from calcore.schema import Timedelta
from calcore.interfaces import IAttendeeSource, IStorageManager
from datetime import datetime

class IDate(Interface):
    """Common base for IYear, IMonth, IDate interfaces.
    """
    
    def getEvents():
        """Get events for the period this object represents.
        """
        pass
    
class IYear(IDate):
    def getYear():
        """The year this object is representing.
        """

    def getMonths():
        """Get a list of months in this year, numerically.
        """

class IMonth(IDate):
    def getYear():
        """The year the month is in.
        """

    def getMonth():
        """The month this object is representing, numerically.
        """

    def getDays():
        """Get a list of days in this month, numerically.
        """

    def getDateForDay(day):
        """Given a day number in this month, return the date.
        """
        
class IEventList(Interface):
    pass
        
class IWeekList(Interface):
    pass

class IWeekYear(Interface):
    """Allows navigating to weeks in a year.
    """
    def getYear():
        """The year this object is representing.
        """

    def getWeeks():
        """Get a list of weeknumbers for this year.
        """

class IWeek(IDate):
    def getYear():
        """The year this week is in.
        """

    def getWeekNr():
        """The ISO weeknumber for this week.
        """

    def getWeekdays():
        """The ISO weekdays in this week, numerically.
        """

    def getDateForWeekday(weekday):
        """Given a weekday, return the datetime for the day.
        """

class IDay(IDate):
    def getYear():
        """Get the year this day is in.
        """

    def getMonth():
        """Get the month this day is in, numerically.
        """

    def getDay():
        """Get the day this object is representing.
        """
class IZopeAttendeeSource(IAttendeeSource):
    """Extends AttendeeSource with things made to support Zope"""
    
    def getMainCalendarForAttendeeId(id):
        """Returns the main calendar for the attendee id
        
        This is used to fetch security settings, which are set on the calendar.
        """
        
    def notifyEventEvent(event):
        """The method that gets called when an event event happens"""


class IZopeStorageManager(IStorageManager):
    """Extends StorageManager with things made to support Zope"""
        
    def notifyEventEvent(event):
        """The method that gets called when an event event happens"""
        
        
class IBusyChecker(Interface):
    """These components are used to check if some attendees are busy
    
    Which attendees are checked depend on the implementation. For example
    a IBusyChecker for an event will check the attendees in the event. An
    IBusyChecker for an add view will check the main attendees of the 
    calendar, and so on. It is used by Widgets, and therefore expected to
    raise sensible WidgetInputErrors if users are busy."""
    
    def check(dtstart, dtend):
        """Check for busyness between the two datetime values"""
        