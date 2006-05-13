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
  month.py
"""

import calendar
from datetime import date, timedelta
from zope.app.zapi import getMultiAdapter
from zope.interface import implements

from AccessControl import getSecurityManager

from interfaces import IUnPositionedView, IEventDisplay

# Some default "constants" for rendering:
CALENDAR_WIDTH = 650
DAY_HEIGHT = 100

class MonthView:
    """Holds the rendering information for month views"""

    implements(IUnPositionedView)

    def calcInfo(self):
        """Calculates all the information necessary for display"""
        self.year = self.context.getYear()
        self.month = self.context.getMonth()

        # store the start date of the month
        self.monthstart = date(self.year, self.month, 1)
        # store a date in the last month
        self.prevmonth = self.monthstart - timedelta(days=1)
        # calculate the start date of the next month
        weekday, days_in_month = calendar.monthrange(self.year, self.month)
        self.nextmonth = self.monthstart + timedelta(days=days_in_month)
        
        # first monday to be displayed
        self.begins = self.monthstart - timedelta(self.monthstart.weekday())
        # last sunday to be displayed
        self.ends = self.nextmonth + timedelta(6 - self.nextmonth.weekday())
        # amount of weeks to display
        self.weeks = int(((self.ends - self.begins).days + 1) / 7)

        # calculate width and height
        self.day_width = CALENDAR_WIDTH / 7
        self.calendar_width = self.day_width * 7

        self.day_height = DAY_HEIGHT
        self.calendar_height = self.day_height * self.weeks
        self.first_week = self.begins.isocalendar()[1]
        
    def getNextMonthUrl(self):
        cal = self.context.getCalendar()
        return "%s/%s/%s" % (
            cal.absolute_url(), self.nextmonth.year, self.nextmonth.month)

    def getPrevMonthUrl(self):
        calendar = self.context.getCalendar()
        return "%s/%s/%s" % (
            calendar.absolute_url(), self.prevmonth.year, self.prevmonth.month)
    
    def getDateForWeekDay(self, week, weekday):
        return self.begins + timedelta(week * 7 + weekday - 1)

    def getOccurrences(self, day):
        occurrences = self.context.getCalendar().getOccurrencesInDay(day)
        displays = [getMultiAdapter([occurrence, self], IEventDisplay) for
                    occurrence in occurrences]
        return displays


    def getCalendarUrl(self):
        return self.context.getCalendar().absolute_url()

    def getTodayInfo(self):
        today = date.today()
        return {'year': today.year, 'month': today.month, 'day': today.day}
   
    def checkPermission(self, permission, object=None):
        if object is None: # Default to the event
            object = self.context
        user = getSecurityManager().getUser()
        return user.has_permission(permission, object)
