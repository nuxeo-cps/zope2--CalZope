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

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest

from zope.app import zapi
from calcore import cal
from datetime import datetime, timedelta

from calendartest import CalendarTestCase
from Products.CalZope.interfaces import IEventList
from calcore.interfaces import IStorageManager
from Products.CalZope.interfaces import IZopeAttendeeSource

class TestNavigation(CalendarTestCase):

    def afterSetUp(self):
        CalendarTestCase.afterSetUp(self)
        self.folder.manage_addProduct['CalZope'].manage_addCalendar(
            'cal', 'Calendar')
        self.cal = self.folder.cal
        self.folder.acl_users._doAddUser(
            'testuser', 'testuser', ['Manager'], [])
        source = zapi.getUtility(IZopeAttendeeSource, context=self.folder)
        self.cal.addAttendee(source.getAttendee('testuser'))
        self.attendee = source.getAttendee('testuser')

    def test_year(self):
        obj = self.cal.unrestrictedTraverse('2005')
        self.assertEquals(2005, obj.getYear())

    def test_month(self):
        obj = self.cal.unrestrictedTraverse('2005/2')
        self.assertEquals(2005, obj.getYear())
        self.assertEquals(2, obj.getMonth())

    def test_day(self):
        obj = self.cal.unrestrictedTraverse('2005/2/10')
        self.assertEquals(2005, obj.getYear())
        self.assertEquals(2, obj.getMonth())
        self.assertEquals(10, obj.getDay())

    def test_week(self):
        obj = self.cal.unrestrictedTraverse('week/2005/8')
        self.assertEquals(2005, obj.getYear())
        self.assertEquals(8, obj.getWeekNr())

    def test_weekday(self):
        obj = self.cal.unrestrictedTraverse('week/2005/8/3')
        self.assertEquals(2005, obj.getYear())
        self.assertEquals(2, obj.getMonth())
        self.assertEquals(23, obj.getDay())

    def test_eventlist(self):
        obj = self.cal.unrestrictedTraverse('event')
        self.assert_(IEventList.providedBy(obj))

    def test_event(self):
        event = self.attendee.createEvent(
            dtstart=datetime(2005, 2, 3, 10, 00),
            duration=timedelta(minutes=60),
            title='An event')
        event_id = event.unique_id
        obj = self.cal.unrestrictedTraverse('event/%s' % event_id)
        self.assertEquals(
            event_id,
            event.unique_id)

    # XXX should add tests for illegal year/month/day combinations etc

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestNavigation),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
