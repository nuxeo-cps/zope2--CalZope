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
  week.py
"""

from datetime import timedelta, datetime, date

from AccessControl import getSecurityManager

from zope.interface import implements
from zope.app.zapi import getMultiAdapter

from calcore import isoweek
from calview import CalendarView
from displaytable import DayGrid
from interfaces import IPositionedView, IEventDisplay

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")

# Some defaults for rendering:
HOUR_HEIGHT = 30 # Two minutes per pixel
CALENDAR_WIDTH = 650

class WeekView(CalendarView):
    """Holds the rendering information for week views"""
    
    implements(IPositionedView)

    def getWeekdays(self):
        return range(1, 8)

    def getDateForWeekday(self, weekday):
        return isoweek.weeknr2datetime(self.year, self.week, weekday)
    
    def calcInfo(self):
        self.calendar = self.context.getCalendar()
        self.week = self.context.getWeekNr()
        self.year = self.context.getYear()
        self.first_day = self.getDateForWeekday(1)
        self.month = self.first_day.month
        # self.ends is the day after the last day
        self.ends = self.first_day + timedelta(8)
        self.days = 7 

        # TODO: Pick up from calendar or tool instead:
        self.from_hour = 8
        self.to_hour = 20
        self.hour_count = self.to_hour - self.from_hour

        # We might want to make this more flexible for different layouts
        # The 650 pixel width is good for the default CPS design on my
        # screen. Not very generic.
        self.day_width = CALENDAR_WIDTH / self.days
        # Make sure they match even if calendar_width isn't a multiple of 7
        self.width = self.day_width * self.days

        self.hour_height = HOUR_HEIGHT
        self.height = self.hour_height * self.hour_count
        # Add on the "before" and "after" lines.
        if self.from_hour != 0:
            self.height = self.height  + self.hour_height 
        if self.to_hour != 24:
            self.height = self.height  + self.hour_height 

    def getDays(self):
        return [self.getDateForWeekday(d) 
                for d in self.getWeekdays()]
            
    def getEventDisplays(self):        
        all_displays = []
        for d in self.context.getWeekdays():
            day = self.context.getDateForWeekday(d) 
            occurrences = self.getOccurrencesInDay(day)
            displays = [getMultiAdapter([occurrence, self], IEventDisplay) for
                        occurrence in occurrences]
            
            # Handle overlapping displays:
            daygrid = DayGrid(0, self.day_width * (d-1), 
                                 self.height,
                                 self.day_width)
            daygrid.extend(displays)
            daygrid.flatten()
            all_displays.extend(daygrid)
            
        return all_displays

    def getTodayInfo(self):
        today = date.today()
        if (today >= self.first_day.date() and 
            today < (self.first_day + timedelta(7)).date()):
            istoday = True
        else:
            istoday = False
        return {'year': today.year, 
                'month': today.month, 
                'day': today.day,
                'istoday': istoday}
 