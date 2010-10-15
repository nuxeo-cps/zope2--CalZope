# -*- coding: iso-8859-15 -*-
# (C) Copyright 2006 Nuxeo SARL <http://nuxeo.com>
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
# $Id: month.py 46089 2006-05-31 15:05:36Z lregebro $
"""
  navigation.py
"""

import calendar
from calcore import isoweek
from datetime import date, timedelta

from Products.Five import BrowserView

from Products.CalZope.interfaces import IYear, IMonth, IWeek, IDay

from widget import calendar_js_template

from zope.i18n import translate
from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")


# View types:
YEAR_VIEW = 'year'
MONTH_VIEW = 'month'
WEEK_VIEW = 'week'
DAY_VIEW = 'day'

class RedirectToLastView(BrowserView):
    
    def __call__(self):
        cal = self.context.getCalendar()
        url = cal.absolute_url()
        # Get the view type and date that should be shown from the
        # session:
        if self.request.form.get('date'):
            year, month, day = self.request.form.get('date').split('-')
            view_date = date(int(year), int(month), int(day))
            view_date = self.request.SESSION['calzope_view_date'] = view_date
        else:
            view_date = self.request.SESSION.get('calzope_view_date', None)
            if view_date is None:
                view_date = date.today()
        view_type = self.request.SESSION.get('calzope_view_type', WEEK_VIEW)
        # No last date, show today
        
        if view_type == YEAR_VIEW:
            view = cal.restrictedTraverse(str(view_date.year))
        elif view_type == MONTH_VIEW:
            view = cal.restrictedTraverse('%s/%s' % (view_date.year, 
                                                     view_date.month))
        elif view_type == WEEK_VIEW:
            year, week, weekday = view_date.isocalendar()
            view = cal.restrictedTraverse('week/%s/%s' % (year, week))
        elif view_type == DAY_VIEW:
            view = cal.restrictedTraverse('%s/%s/%s' % (view_date.year, 
                                                        view_date.month,
                                                        view_date.day))
        else:
            raise ValueError("Unknown view_type " + view_type)
        url = view.absolute_url()
        if self.request.has_key('portal_status_message'):
            url = url + '?portal_status_message=' + self.request['portal_status_message']
        response = self.request.RESPONSE
        response.redirect(url)
    

class NavigationView:
    """Basic view for navigational support"""
    
    yearTabClass = "unselected"
    monthTabClass = "unselected"
    weekTabClass = "unselected"
    dayTabClass = "unselected"
    todayTabClass  = "unselected"
    
    def __init__(self, context, request):
        """ttw"""
        self.context = context
        self.request = request
        self.calendar = self.context.getCalendar()
        self.today = date.today()
        
        # Get the last date shown from the session:
        view_date = self.request.SESSION.get('calzope_view_date', None)
        # No last date, show today
        if view_date is None:
            view_date = self.today
            
        # Set the default view date info (to be changed by calcDate()
        self.setViewData(view_date)
                
        # Recalculate which date really is shown. calcDate changes the
        # year, month and day attributes on the view accordingly:
        new_date = self.calcDate()
        self.setViewData(new_date)
        
        # Select the today tab if today is in the view:
        if self.todayInView():
            self.todayTabClass = "selected"
        
        # calInfo often sets new date info (year/month/day) on the view. 
        # This should be stored in the session:
        self.request.SESSION['calzope_view_date'] = new_date
        # This is used by the redirect views to select the view type:
        self.request.SESSION['calzope_view_type'] = self.view_type
        
    def calcDate(self):
        raise NotImplementedError('NavigationView must be subclassed')

    def todayInView(self):
        raise NotImplementedError('NavigationView must be subclassed')

    def getNextViewUrl(self):
        raise NotImplementedError('NavigationView must be subclassed')

    def getPrevViewUrl(self):
        raise NotImplementedError('NavigationView must be subclassed')

    def getTodayViewUrl(self):
        raise NotImplementedError('NavigationView must be subclassed')

    def setViewData(self, dt):
        self.view_date = dt
        self.year = dt.year
        self.month = dt.month
        self.month_name = translate(_('calendar_month_%s' % self.month), 
                                    context=self.request)
        self.day = dt.day
        self.long_date = self.getLongDateFormat() % {'day': self.day,
                                                     'month': self.month_name,
                                                     'year': self.year}
        week_info = dt.isocalendar()
        self.week_year = week_info[0]
        self.week = week_info[1]
        self.week_day = week_info[2]

    def getDateForWeekDay(self, week, weekday):
        return self.begins + timedelta(week * 7 + weekday - 1)

    def getCalendarUrl(self):
        return self.context.getCalendar().absolute_url()
        
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

    def getDateFormat(self):
        return translate(_('%Y-%m-%d'), context=self.request)

    def getLongDateFormat(self):
        return translate(_('%(day)s %(month)s %(year)s'), context=self.request)

class YearNavigationView(NavigationView):
    """The navigation view for year views"""
    
    view_type = YEAR_VIEW
    yearTabClass = "selected"
    
    def calcDate(self):
        """Recalculates which day should be shown"""        
        return date(self.context.getYear(), self.month, self.day)
        
    def todayInView(self):
        return self.today.year == self.year
    
    def getPrevViewUrl(self):
        return "%s/%s" % (self.calendar.absolute_url(), str(self.year - 1))

    def getNextViewUrl(self):
        return "%s/%s" % (self.calendar.absolute_url(), str(self.year + 1))

    def getTodayViewUrl(self):
        return "%s/%s" % (self.calendar.absolute_url(), str(self.today.year))


class MonthNavigationView(NavigationView):
    """The navigation view for month views"""
    
    view_type = MONTH_VIEW
    monthTabClass = "selected"
    
    def calcDate(self):
        """Recalculates which day should be shown"""
        try:
            return date(self.context.getYear(), 
                        self.context.getMonth(), 
                        self.day)
        except ValueError:
            # The day is out of range. Lower the day with one and try again
            # recursively until it works (four times, in the worst case):
            self.day -= 1
            return self.calcDate()

    def todayInView(self):
        return self.today.year == self.year and self.today.month == self.month
    
    def getPrevViewUrl(self):
        year = self.year
        month = self.month - 1
        if month < 1:
            month +=12
            year -= 1
        return "%s/%s/%s" % (self.calendar.absolute_url(), year, month)

    def getNextViewUrl(self):
        year = self.year
        month = self.month + 1
        if month > 12:
            month -= 12
            year += 1
        return "%s/%s/%s" % (self.calendar.absolute_url(), year, month)

    def getTodayViewUrl(self):
        return "%s/%s/%s" % (self.calendar.absolute_url(), 
                             self.today.year, 
                             self.today.month)


class WeekNavigationView(NavigationView):
    """The navigation view for month views"""
    
    view_type = WEEK_VIEW
    weekTabClass = "selected"
    
    def calcDate(self):
        """Recalculates which day should be shown"""
        first_day = self.context.getDateForWeekday(1).date()
        last_day = self.context.getDateForWeekday(7).date()
        view_date = self.view_date
        if view_date >= first_day and view_date <= last_day:
            # The current day is in this week. Don't change it:
            return self.view_date
        
        # We changed the week number, but will keep the week day,
        # so that current day will go from sa, wednesday to 
        # wednesday when browsing weeks.
        return self.context.getDateForWeekday(self.week_day).date()
        
    def todayInView(self):
        year, week, day = self.today.isocalendar()
        return year == self.year and week == self.week
    
    def getPrevViewUrl(self):
        prevweek = self.week - 1
        if prevweek < 1:
            prevyear = self.week_year - 1
            prevweek = isoweek.getWeeksInYear(prevyear)
        else:
            prevyear = self.week_year
            
        return "%s/week/%s/%s" % (
            self.calendar.absolute_url(), prevyear, prevweek)

    def getNextViewUrl(self):
        nextweek = self.week + 1
        if nextweek > isoweek.getWeeksInYear(self.week_year):
            nextweek = 1
            nextyear = self.week_year + 1
        else:
            nextyear = self.week_year    

        return "%s/week/%s/%s" % (
            self.calendar.absolute_url(), nextyear, nextweek)

    def getTodayViewUrl(self):
        year, week, day = self.today.isocalendar()
        return "%s/week/%s/%s" % (self.calendar.absolute_url(), year, week)

class DayNavigationView(NavigationView):
    """The navigation view for month views"""
    
    view_type = DAY_VIEW
    dayTabClass = "selected"
    
    def calcDate(self):
        """Recalculates which day should be shown"""        
        year = self.context.getYear()
        month = self.context.getMonth()
        day = self.context.getDay()
        return date(year, month, day)
                
    def todayInView(self):
        return (self.today.year == self.year and 
                self.today.month == self.month and
                self.today.day == self.day)
    
    def getPrevViewUrl(self):
        yesterday = date(self.year, self.month, self.day) - timedelta(1)
        return "%s/%s/%s/%s" % (self.calendar.absolute_url(), 
                                yesterday.year, 
                                yesterday.month, 
                                yesterday.day)

    def getNextViewUrl(self):
        tomorrow = date(self.year, self.month, self.day) + timedelta(1)
        return "%s/%s/%s/%s" % (self.calendar.absolute_url(), 
                                tomorrow.year, 
                                tomorrow.month, 
                                tomorrow.day)

    def getTodayViewUrl(self):
        return "%s/%s/%s/%s" % (self.calendar.absolute_url(), 
                                self.today.year, 
                                self.today.month,
                                self.today.day)
