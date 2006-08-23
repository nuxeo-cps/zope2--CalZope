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

from calview import CalendarView
from widget import make_calendar_js

class MonthView(CalendarView):
    """Holds the rendering information for month views"""

    implements(IUnPositionedView)
    
    # A month view has a very limited amount of space:
    display_max_events = 5

    def calcInfo(self):
        """Calculates all the information necessary for display"""
        self.calendar = self.context.getCalendar()
        self.year = self.context.getYear()
        self.month = self.context.getMonth()

        # store the start date of the month
        self.monthstart = date(self.year, self.month, 1)
        # calculate the start date of the next month
        weekday, days_in_month = calendar.monthrange(self.year, self.month)
        self.nextmonth = self.monthstart + timedelta(days=days_in_month)
        
        # first monday to be displayed
        self.begins = self.monthstart - timedelta(self.monthstart.weekday())
        # last sunday to be displayed
        self.ends = self.nextmonth + timedelta(6 - self.nextmonth.weekday())
        # amount of weeks to display
        self.weeks = int(((self.ends - self.begins).days + 1) / 7)

        self.first_week = self.begins.isocalendar()[1]

        # A per viewing cache of which days that have more events than can
        # be displayed, just to avoid searching each day twice.
        self.date_display_maxed = {}
            
    def getDateForWeekDay(self, week, weekday):
        return self.begins + timedelta(week * 7 + weekday - 1)

    def getOccurrenceDisplays(self, day):
        occurrences = self.calendar.getOccurrencesInDay(day)
        count = 0
        self.date_display_maxed[day] = 0
        displays = []
        for occurrence in occurrences:
            count += 1
            if count > self.display_max_events:
                self.date_display_maxed[day] = 1
                break
            displays.append(getMultiAdapter([occurrence, self], IEventDisplay))
        # Cut off the last one (to be replaced by a More... tag)
        if self.date_display_maxed[day] == 1:
            displays = displays[:-1]
        return displays
    
    def hasMoreEvents(self, day):
        """Returns true if there are more events than can be displayed"""
        if not self.date_display_maxed.has_key(day):
            # We haven't checked yet:
            self.getOccurrenceDisplays(day)            
        return self.date_display_maxed[day]

    def getTodayInfo(self):
        today = date.today()
        if today.year == self.year and today.month == self.month:
            istoday = True
        else:
            istoday = False
        return {'year': today.year, 
                'month': today.month, 
                'day': today.day,
                'istoday': istoday}
    
    def getClassForDate(self, dt):
        if dt.month == self.context.getMonth():
            class_ = 'thisMonth'
        else:
            class_ = 'otherMonth'
        if len(self.calendar.getOccurrencesInDay(dt)) != 0:
            class_ += 'HasEvent'
        else:
            class_ += 'NoEvent'
        return class_
        