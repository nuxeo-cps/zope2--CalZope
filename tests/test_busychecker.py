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
# $Id: test_usecase.py 31373 2006-01-06 14:30:09Z lregebro $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# a duplication from usecase.txt in CalCore,
# but hard to reuse doctests in Zope 2 context..
import unittest
from datetime import datetime, timedelta, date

from zope.app import zapi

from calendartest import CalendarTestCase
from calcore import cal, recurrent
from calcore.interfaces import IStorageManager
from Products.CalZope.interfaces import IZopeAttendeeSource
from Products.CalZope.zopecal import BaseBusyChecker
from Products.CalZope.zopecal import BusyUsersError, BusyUserError

class TestBusyChecker(CalendarTestCase):
    
    def afterSetUp(self):
        CalendarTestCase.afterSetUp(self)
        source = zapi.getUtility(IZopeAttendeeSource, context=self.folder)
        # Create a load of users and events
        self.folder.acl_users._doAddUser(
            'testmgr', 'testmgr', ['Manager'], [])
        self.folder.acl_users._doAddUser(
            'testuser', 'testuser', [], [])
        self.testmgr = source.getAttendee('testmgr')
        self.testuser = source.getAttendee('testuser')
        self.testmgr.createEvent(
            dtstart=datetime(2005, 4, 10, 10, 00),
            duration=timedelta(minutes=60),
            status='CONFIRMED',
            title="Confirmed event will block")
        self.testmgr.createEvent(
            dtstart=datetime(2005, 4, 10, 12, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Waiting event will not block")
        self.testmgr.createEvent(
            dtstart=datetime(2005, 4, 10, 13, 00),
            duration=timedelta(minutes=60),
            status='CONFIRMED',
            transparent=True,
            title="Transparent event will not block")
        event = self.testmgr.createEvent(
            dtstart=datetime(2005, 4, 10, 14, 00),
            duration=timedelta(minutes=60),
            status='CONFIRMED',
            title="Unaccepted events do not block")
        event.setParticipationStatus(self.testmgr, 'TENTATIVE')
        self.testuser.createEvent(
            dtstart=datetime(2005, 4, 10, 15, 00),
            duration=timedelta(minutes=60),
            status='CONFIRMED',
            title="This will be overridden by the manager")

        
    def test_busychecker(self):
        self.login('testuser')
        
        checker = BaseBusyChecker()
        checker.context = self.folder
        checker.attendees = [self.testmgr.getAttendeeId()]
        checker.ignore_events = []
        
        # This time is free, it should not raise anything
        checker.check(datetime(2005, 4, 10, 11, 00), 
                      datetime(2005, 4, 10, 12, 00))
        
        # This time is busy, it should raise an error
        self.assertRaises(BusyUsersError, checker.check, 
                          datetime(2005, 4, 10, 10, 00), 
                          datetime(2005, 4, 10, 11, 00))
        
        # This time has an event, but it is not accepted, 
        # it should not raise an error
        checker.check(datetime(2005, 4, 10, 12, 00), 
                      datetime(2005, 4, 10, 13, 00))

        # This time has an accepted event, but it is transparent, 
        # it should not raise an error
        checker.check(datetime(2005, 4, 10, 13, 00), 
                      datetime(2005, 4, 10, 14, 00))

        # This time has an accepted event, non-transparent event, 
        # but the user has not accepted. It should not raise an error:
        checker.check(datetime(2005, 4, 10, 14, 00), 
                      datetime(2005, 4, 10, 15, 00))

        # If you try to double book yourself, you should get an error:
        checker.attendees = [self.testuser.getAttendeeId()]
        self.assertRaises(BusyUserError, checker.check,
                          datetime(2005, 4, 10, 15, 00), 
                          datetime(2005, 4, 10, 16, 00))
        
        # However, somebody who is a manager, should not:
        self.login('testmgr')
        checker.check(datetime(2005, 4, 10, 15, 00), 
                      datetime(2005, 4, 10, 16, 00))

    def test_recurringblock1(self):
        # Recurring events caused the BusyChecker
        # to block EVERYTHING after the start of that event.
        self.login('testmgr')
        
        checker = BaseBusyChecker()
        checker.context = self.folder
        checker.attendees = [self.testmgr.getAttendeeId()]
        checker.ignore_events = []

        self.testmgr.createEvent(
            dtstart=datetime(2006, 4, 10, 10, 00),
            duration=timedelta(minutes=60),
            status='CONFIRMED',
            title="Recurring event will block only during the event",
            recurrence=recurrent.DailyRecurrenceRule())

        # Not busy the day before:
        checker.check(datetime(2006, 4, 9, 10, 00), 
                      datetime(2006, 4, 9, 11, 00))
        # Not busy in the afternoons:
        checker.check(datetime(2006, 4, 15, 14, 00), 
                      datetime(2006, 4, 15, 15, 00))
        
        # Is busy when it happens:
        self.assertRaises(BusyUserError, checker.check,
                          datetime(2006, 4, 16, 10, 00), 
                          datetime(2006, 4, 16, 11, 00))

        self.testmgr.createEvent(
            dtstart=datetime(2005, 4, 10, 10, 00),
            duration=timedelta(minutes=60),
            status='CONFIRMED',
            title="Recurring event will also block only during the event",
            recurrence=recurrent.DailyRecurrenceRule(
                until=date(2005,4,25)))

        # Not busy the day before:
        checker.check(datetime(2005, 4, 9, 10, 00), 
                      datetime(2005, 4, 9, 11, 00))
        # Not busy in the afternoons:
        checker.check(datetime(2005, 4, 15, 14, 00), 
                      datetime(2005, 4, 15, 15, 00))
        
        # Is busy when it happens:
        self.assertRaises(BusyUserError, checker.check,
                          datetime(2005, 4, 16, 10, 00), 
                          datetime(2005, 4, 16, 11, 00))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestBusyChecker),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
