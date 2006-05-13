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

class TestUsecase(CalendarTestCase):
    
    def test_usecase(self):
        m = zapi.getUtility(IStorageManager, context=self.folder)
        s = zapi.getUtility(IZopeAttendeeSource, context=self.folder)
        for username in ['martijn', 'florent', 'bob']:
            self.folder.acl_users._doAddUser(
                username, username, ['Manager'], [])
        martijn = s.getAttendee('martijn')
        florent = s.getAttendee('florent')
        bob = s.getAttendee('bob')
        
        meeting = florent.createEvent(
            dtstart=datetime(2005, 4, 10, 16, 00),
            duration=timedelta(minutes=60),
            status='TENTATIVE',
            title="Florent's Meeting")

        april = (datetime(2005, 4, 1), datetime(2005, 5, 1))
        events = florent.getEvents(april)
        self.assertEquals(1, len(events))
        self.assertEquals(meeting, events[0])
        self.assertEquals("Florent's Meeting", events[0].title)
        self.assertEquals('ACCEPTED',
                          events[0].getParticipationStatus(florent))

        self.assertEquals([], martijn.getEvents(april))
        self.assertEquals([], bob.getEvents(april))
        #self.assertEquals([], room1.getEvents(april))

        
        meeting.invite([martijn, bob]) # room1

        result = []
        for attendee in [martijn, bob]: # room1
            events = attendee.getEvents(april)
            result.append(events[0] == meeting)
        self.assertEquals([True, True], result)

        self.assertEquals(
            ['NEEDS-ACTION', 'NEEDS-ACTION'],
            [meeting.getParticipationStatus(attendee) for attendee in 
             [martijn, bob]])

        # self.assertEquals('ACCEPTED', meeting.getParticipationStatus(room1))

        events = martijn.getEvents(
            april, 
            cal.SearchCriteria(participation_status='NEEDS-ACTION'))
        self.assertEquals(1, len(events))
        self.assertEquals("Florent's Meeting", events[0].title)

        events[0].setParticipationStatus(martijn, 'ACCEPTED')
        self.assertEquals(
            'ACCEPTED', events[0].getParticipationStatus(martijn))
        
        self.assertEquals([],
                          martijn.getEvents(
            april, 
            cal.SearchCriteria(participation_status='NEEDS-ACTION')))
        

        meeting.invite([martijn])
        self.assertEquals('ACCEPTED', meeting.getParticipationStatus(martijn))
    
        events = florent.getOrganizedEvents()
        self.assertEquals(1, len(events))
        self.assertEquals("Florent's Meeting", events[0].title)
        m.deleteEvent(events[0])
        events = florent.getOrganizedEvents()
        self.assertEquals(0, len(events))
                          

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestUsecase),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
