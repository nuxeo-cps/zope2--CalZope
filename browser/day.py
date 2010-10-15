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
  day.py
"""

from datetime import timedelta, date

from zope.interface import implements
from zope.app.zapi import getMultiAdapter

from AccessControl import getSecurityManager

from displaytable import DayGrid
from interfaces import IPositionedView, IEventDisplay
from widget import make_calendar_js
from calview import CalendarView

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")

# Some defaults for rendering:
HOUR_HEIGHT = 30 # Two minutes per pixel
CALENDAR_WIDTH = 650

class DayView(CalendarView):
    """Holds the rendering information for day views"""
    
    implements(IPositionedView)
               
    def calcInfo(self):
        self.day = self.context.getDay()
        self.month = self.context.getMonth()
        self.year = self.context.getYear()
        self.first_day = date(self.year, self.month, self.day)
        self.week = self.first_day.isocalendar()[1]
        self.days = 1

        # TODO: Pick up from calendar or tool instead:
        self.from_hour = 8
        self.to_hour = 20
        self.hour_count = self.to_hour - self.from_hour

        # We might want to make this more flexible for different layouts
        # The 650 pixel width is good for the default CPS design on my
        # screen. Not very generic.
        self.day_width = self.width = CALENDAR_WIDTH
        self.hour_height = HOUR_HEIGHT
        self.height = self.hour_height * self.hour_count
        # Add on the "before" and "after" lines.
        if self.from_hour != 0:
            self.height = self.height  + self.hour_height 
        if self.to_hour != 24:
            self.height = self.height  + self.hour_height 

    def getDate(self):
        return self.first_day
    
    def getEventDisplays(self):
        context = self.context
        day = date(context.getYear(), context.getMonth(), context.getDay())
        occurrences = self.context.getCalendar().getOccurrencesInDay(day)
        displays = [getMultiAdapter([occurrence, self], IEventDisplay)
                  for occurrence in occurrences]
        
        # Handle overlapping displays:
        daygrid = DayGrid(0, 0, self.height, self.day_width)
        daygrid.extend(displays)
        daygrid.flatten()
        
        return daygrid

    def getTodayInfo(self):
        today = date.today()
        if today == self.first_day:
            istoday = True
        else:
            istoday = False
        return {'year': today.year, 
                'month': today.month, 
                'day': today.day,
                'istoday': istoday}
     