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
# $Id: test_usecase.py 26193 2005-08-29 10:51:26Z lregebro $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# a duplication from usecase.txt in CalCore,
# but hard to reuse doctests in Zope 2 context..
import unittest
from datetime import datetime, timedelta

from zope.app import zapi

from calendartest import CalendarTestCase
from calcore import cal, recurrent
from calcore.interfaces import IStorageManager
from Products.CalZope.interfaces import IZopeAttendeeSource

class TestAllDay(CalendarTestCase):
    
    def afterSetUp(self):
        CalendarTestCase.afterSetUp(self)

        self.folder.acl_users._doAddUser('martijn', 'martijn', ['Manager'], [])
        source = zapi.getUtility(IZopeAttendeeSource, context=self.folder)
        self._martijn = source.getAttendee('martijn')
        
    def test_allday(self):
        alldayevent = self._martijn.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(minutes=60),
            status='CONFIRMED',
            title="An all day event",
            allday=True)
        # Should show up here:
        self.failUnlessEqual(alldayevent.duration, timedelta(1))
        events = self._martijn.getEvents(
            (datetime(2005, 4, 1), datetime(2005, 5, 1)))
        self.assertEquals(1, len(events))
        events = self._martijn.getEvents(
            (datetime(2005, 4, 8), datetime(2005, 4, 12)))
        self.assertEquals(1, len(events))
        events = self._martijn.getEvents(
            (datetime(2005, 4, 10), datetime(2005, 4, 11)))
        self.assertEquals(1, len(events))
        
        events = self._martijn.getEvents(
            (datetime(2005, 4, 3), datetime(2005, 4, 10)))
        self.assertEquals(0, len(events))
        events = self._martijn.getEvents(
            (datetime(2005, 4, 11), datetime(2005, 4, 12)))
        self.assertEquals(0, len(events))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestAllDay),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
