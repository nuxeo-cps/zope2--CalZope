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
# $Id: test_usecase.py 24820 2005-07-12 11:13:31Z lregebro $

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

class TestRecurrence(CalendarTestCase):
    
    def test_usecase(self):
        m = zapi.getUtility(IStorageManager, context=self.folder)
        s = zapi.getUtility(IZopeAttendeeSource, context=self.folder)
        # We test this here to make sure the ZODBStorage indexing works
        florent = s.getAttendee('florent')
        martijn = s.getAttendee('martijn')

        march = (datetime(2005, 3, 1), datetime(2005, 4, 1))
        april = (datetime(2005, 4, 1), datetime(2005, 5, 1))
        may   = (datetime(2005, 5, 1), datetime(2005, 6, 1))

        # Unbounded:
        event = florent.createEvent(
            dtstart=datetime(2005, 4, 10, 20, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Florent's Favourite TV-show",
            recurrence=recurrent.WeeklyRecurrenceRule())
            
        # Bounded
        event = martijn.createEvent(
            dtstart=datetime(2005, 4, 11, 20, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Martijn alarm call",
            recurrence=recurrent.DailyRecurrenceRule(count=5))

        # Test the unbounded event

        events = florent.getEvents(march)
        self.assertEquals(0, len(events))
        events = florent.getEvents(april)
        self.assertEquals(1, len(events))
        events = florent.getEvents(may)
        self.assertEquals(1, len(events))

        events = florent.getOccurrences(april)
        self.assertEquals(3, len(events))
        events = florent.getOccurrences(may)
        self.assertEquals(5, len(events))

        # Test the bounded event
        events = martijn.getEvents(march)
        self.assertEquals(0, len(events))
        events = martijn.getEvents(april)
        self.assertEquals(1, len(events))
        events = martijn.getEvents(may)
        self.assertEquals(0, len(events))

        events = martijn.getOccurrences(april)
        self.assertEquals(5, len(events))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestRecurrence),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
