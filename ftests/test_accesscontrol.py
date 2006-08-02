# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Lennart Regebro <regebro@nuxeo.com>
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
# $Id: test_accesscontrol.py 23793 2005-06-10 16:09:02Z lregebro $
"""
  CalZope Functional Tests
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))
   
import unittest
from datetime import datetime
from calendartest import CalendarTestCase, user_id, manager_id

class testAccessControl(CalendarTestCase):
    
    def test_calendarView(self):
        # Pages with view access:
        pages = ['',
                 'calendar.ics',
                 'calendar.html',
                 '2005',
                 '2005/05',
                 '2005/05/11',
                 'week',
                 'week/2005/5',
                 '2005/05/11/calendar.html',
                 'week/calendar.html',
                 'week/2005/5/calendar.html',                ]

        for page in pages:
            # You can view your calendar 
            response = self.publish(
                '%s/%s' % (self.usercalpath, page),
                basic='%s:secret' % user_id,
                extra={'SESSION':{}}) # SESSION is used by the meetinghelper.
            self.assertResponse(response, (200, 302), 'Page %s' % page)

            # But not anybody elses.
            response = self.publish(
                '%s/%s' % (self.managercalpath, page),
                basic='%s:secret' % user_id)
            self.assertResponse(response, 401, 'Page %s' % page)
        
        # However, if you are AttendeeReader, you can:
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeReader'])
        for page in pages:
            # You can view your calendar 
            response = self.publish(
                '%s/%s' % (self.managercalpath, page),
                basic='%s:secret' % user_id,
                extra={'SESSION':{}}) # SESSION is used by the meetinghelper.
            self.assertResponse(response, (200, 302), 'Page %s' % page)
        

    def test_pagesWithManagerAccess(self):
        pages = ['edit.html',
                 'meetinghelper.html', 
                 'import.html',
                 ]

        for page in pages:
            # You can view your own calendar 
            response = self.publish(
                '%s/%s' % (self.usercalpath, page),
                basic='%s:secret' % user_id,
                extra={'SESSION':{}}) # SESSION is used by the meetinghelper.
            self.assertResponse(response, (200, 302), 'Page %s' % page)

            # But not anybody elses.
            response = self.publish(
                '%s/%s' % (self.managercalpath, page),
                basic='%s:secret' % user_id)
            self.assertResponse(response, 401, 'Page %s' % page)

        # Not even as AttendeeReader
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeReader'])
        for page in pages:
            # You can view your calendar 
            response = self.publish(
                '%s/%s' % (self.managercalpath, page),
                basic='%s:secret' % user_id,
                extra={'SESSION':{}}) # SESSION is used by the meetinghelper.
            self.assertResponse(response, 401, 'Page %s' % page)

        # But as AttendeeManager you can
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeManager'])
        for page in pages:
            # You can view your calendar 
            response = self.publish(
                '%s/%s' % (self.managercalpath, page),
                basic='%s:secret' % user_id,
                extra={'SESSION':{}}) # SESSION is used by the meetinghelper.
            self.assertResponse(response, (200, 302), 'Page %s' % page)

    def test_overviewPages(self):
        # Here is a bunch of pages which I should not be able to view
        # in other peoples calendars, unless I have ManageParticipationStatus,
        # which I get with the AttendeeManager role.
        pages = ['organized_events.html', 
                 'action_needed_events.html',
                 'attended_events.html',
                 #'meetinghelper.html', #Not testing the meeting helper because I get a SESSION error
                ]

        # My own calendar works:
        self.app.REQUEST.SESSION = {}
        for page in pages:
            response = self.publish(
                '%s/%s' % (self.usercalpath, page),
                basic='%s:secret' % user_id)
            self.assertResponse(response, 200, 'Page %s' % page)
            
        # Somebody elses calendar does not work:
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeReader'])
        for page in pages:
            response = self.publish(
                '%s/%s' % (self.managercalpath, page),
                basic='%s:secret' % user_id)
            self.assertResponse(response, 401, 'Page %s' % page)
        
        # Unless I'm a AttendeeManager
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeManager'])
        for page in pages:
            response = self.publish(
                '%s/%s' % (self.managercalpath, page),
                basic='%s:secret' % user_id)
            self.assertResponse(response, 200, 'Page %s' % page)


    def test_eventAddAndView(self):
        # I can't even view the addevent page in another calendar, even if I
        # can view the calendar.
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['WorkspaceReader'])
        response = self.publish(
            '/%s/+/addevent.html' % self.managercalpath,
            basic='%s:secret' % user_id)
        self.assertResponse(response, 401)

        # But I can create an event in my calendar, of course
        response = self.publish(
            '%s/+/addevent.html' % self.usercalpath,
            basic='%s:secret' % user_id,
            extra={'form': {'field.dtstart': '04/01/2005',
                            'field.dtstart_hour': '10',
                            'field.dtstart_minute': '30',
                            'field.dtend': '04/01/2005',
                            'field.dtend_hour': '10',
                            'field.dtend_minute': '35',
                            'field.title': 'testevent',
                            'field.status': 'CONFIRMED',
                            'field.access': 'PRIVATE',
                            'UPDATE_SUBMIT': 'Add'},
                    'SESSION':{}})
        self.assertResponse(response, 302) # This add form redirects if it works
        
        event = self.folder.user_cal.getEvents(
            (datetime(2005,04,01), datetime(2005,04,02)))[0]
        event_id = event.unique_id
        
        # I should be able to view this event in my calendar
        response = self.publish(
            '%s/event/%s' % (self.usercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 200)


    def test_attendeeReader(self):
        # Create an event in the managers calendar
        response = self.publish(
            '%s/+/addevent.html' % self.managercalpath,
            basic='%s:secret' % manager_id,
            extra={'form': {'field.dtstart': '04/01/2005',
                            'field.dtstart_hour': '10',
                            'field.dtstart_minute': '30',
                            'field.dtend': '04/01/2005',
                            'field.dtend_hour': '10',
                            'field.dtend_minute': '35',
                            'field.title': 'testevent',
                            'field.status': 'CONFIRMED',
                            'field.access': 'PUBLIC',
                            'UPDATE_SUBMIT': 'Add'},
                    'SESSION': {}})
        self.assertResponse(response, 302) # This add form redirects if it works

        # Find the event id
        event = self.folder.manager_cal.getEvents(
            (datetime(2005,04,01), datetime(2005,04,02)))[0]
        event_id = event.unique_id

        # The user can not view this event
        response = self.publish(
            '%s/event/%s' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 401)

        # Make the user AttendeeReader, and he can view it
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeReader'])
        response = self.publish(
            '%s/event/%s' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 200)

        # Still should not be able to edit it:
        response = self.publish(
            '%s/event/%s/edit.html' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 401)
        response = self.publish(
            '%s/event/%s/recurrence.html' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 401)

    def test_privatePublic(self):
        # Create an event in the managers calendar
        response = self.publish(
            '%s/+/addevent.html' % self.managercalpath,
            basic='%s:secret' % manager_id,
            extra={'form': {'field.dtstart': '04/01/2005',
                            'field.dtstart_hour': '10',
                            'field.dtstart_minute': '30',
                            'field.dtend': '04/01/2005',
                            'field.dtend_hour': '10',
                            'field.dtend_minute': '35',
                            'field.title': 'testevent',
                            'field.status': 'CONFIRMED',
                            'field.access': 'PUBLIC',
                            'UPDATE_SUBMIT': 'Add'},
                    'SESSION':{}}) # SESSION is used by the meetinghelper.
        self.assertResponse(response, 302) # This add form redirects if it works

        # Find the event id
        event = self.folder.manager_cal.getEvents(
            (datetime(2005,04,01), datetime(2005,04,02)))[0]
        event_id = event.unique_id

        # A nobody can't vbiew this:
        response = self.publish(
            '%s/event/%s' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 401)
        
        # But Attendeereaders can:
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeReader'])
        response = self.publish(
            '%s/event/%s' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 200)

        # Make the event private
        event.access = 'PRIVATE'
        # The AttendeeReader no longer should be able to view the event
        response = self.publish(
            '%s/event/%s' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 401)
        
        # But make him an AttendeeManager, and he can
        self.folder.manager_cal.manage_addLocalRoles(
            user_id, ['AttendeeManager'])
        response = self.publish(
            '%s/event/%s' % (self.managercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 200)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(testAccessControl),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
