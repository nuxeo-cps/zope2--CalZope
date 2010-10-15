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
# $Id: test_navigation.py 24820 2005-07-12 11:13:31Z lregebro $

import unittest
from Testing.ZopeTestCase import ZopeTestCase, installProduct, sandbox
import transaction

installProduct('CalCore')
installProduct('CalZope')
installProduct('Five')

from calcore import cal
from datetime import datetime, timedelta

MAXEVENTS = 20000
MAXRANGE = range(0, MAXEVENTS)

class BasePerformanceTest(sandbox.Sandboxed, ZopeTestCase):
    
    def afterSetUp(self):
        self.folder.manage_addProduct['CalZope'].manage_addCalendarTool()
        for id in ('user1', 'user2', 'user3'):
            self.folder.acl_users._doAddUser(
                id, id, ['Manager'], [])
        self.setUpStorage()
        self.createEvents()

    def setUpStorage(self):
        raise NotImplementedError, "You must override setUpStorage()"
    
    def createEvents(self):
        print "Number of events this test:", MAXEVENTS
        storagemgr = self.folder.portal_calendar.storage_manager
        attendeesrc = self.folder.portal_calendar.attendee_source
        user1 = attendeesrc.getAttendee('user1')
        user2 = attendeesrc.getAttendee('user2')
        user3 = attendeesrc.getAttendee('user3')
        
        # Create loads and loads of events. First User 1 and 2:
        self._startdate = datetime(2005, 4, 1, 8, 0)
        basedate =  self._startdate
        before = datetime.now()
        for x in MAXRANGE:
            dtstart = basedate + timedelta(hours=x%11)
            duration = timedelta(hours=1+x%3)
            uid = 'event' + str(x)
            event = storagemgr.createEvent(uid, dtstart=dtstart, 
                                           duration=duration, title=uid)
            # Determine who gets invited:
            # User 1 has very many events:
            if x%3:
                event.invite([user1])
            # User 2 many as well, but still less:
            if x%2:
                event.invite([user2])
            # User 3 has very few events:
            # (Each 97th is because 97 is a prime. I like primes for this, as
            ## they make for very long non-repeating sequences.)
            if not x%97: 
                event.invite([user3])
            # Increase to next day
            if not x%40:
                basedate = basedate + timedelta(1)
                
            if not (x+1)%10000:
                # Time for a transaction commit.
                #print "Commiting events to db after %s events" % (x+1)
                transaction.commit()
        
        # Make sure all events are in the ZODB.
        transaction.commit()

        self._testduration = basedate - self._startdate
        after = datetime.now()
        duration = after - before
        print "       Create Events:", duration
        print "           per event:", duration/MAXEVENTS
        
    def test_getEvents(self):
        storagemgr = self.folder.portal_calendar.storage_manager
        attendeesrc = self.folder.portal_calendar.attendee_source

        # First, get all events, one at a time, by id
        # This should be rather quick
        # XXX Yes it is really quick, even with big sets, so it's says
        # nothing useful, and is commented out.

        #before = datetime.now()
        #for x in MAXRANGE:
            #id = 'event'+str(x)
            #event = storagemgr.getEvent(id)
            #self.failUnlessEqual(event.title, id)
        #after = datetime.now()
        #duration = after - before
        #print "     Get event by id:", duration
        #print "            per call:", duration/MAXEVENTS
    
        # Then get the events by period. This is will take a long time
        # with unoptimized storages
        storagemgr = self.folder.portal_calendar.storage_manager
        number_of_tests = 10
        delta = self._testduration / (number_of_tests*4)
        startdate = self._startdate + (self._testduration*3/4)
        
        # A spread the tests evently during the last quarter of the total
        # event space. Most views will be made with most events already 
        # passed 
        dtstart = startdate
        before = datetime.now() 
        for x in range(0, number_of_tests):
            dtend = dtstart + timedelta(30)
            events = storagemgr.getEvents((dtstart, dtend))
            dtstart = dtstart + delta
        after = datetime.now()
        duration = after - before
        print "Get events by period:", duration
        print "            per call:", duration/number_of_tests
 
        # This one is the most important, at this is the one that is done
        # with every request when you look at a calendar. We test this with
        # month long duration, as that is likely to take a bit longer.
        dtstart = startdate
        user1 = attendeesrc.getAttendee('user1')
        before = datetime.now()
        searchcriteria = cal.SearchCriteria(user1)
        for x in range(0, number_of_tests):
            dtend = dtstart + timedelta(30)
            events = storagemgr.getOccurrencesSegmented((dtstart, dtend), 
                                                        searchcriteria)
            dtstart = dtstart + delta
        after = datetime.now()
        duration = after - before
        print "   Get occurrences 1:", duration
        print "            per call:", duration/number_of_tests

        dtstart = startdate
        user3 = attendeesrc.getAttendee('user3')
        before = datetime.now()
        searchcriteria = cal.SearchCriteria(user3)
        for x in range(0, number_of_tests):
            dtend = dtstart + timedelta(30)
            events = storagemgr.getOccurrencesSegmented((dtstart, dtend), 
                                                        searchcriteria)
            dtstart = dtstart + delta
        after = datetime.now()
        duration = after - before
        print "   Get occurrences 2:", duration
        print "            per call:", duration/number_of_tests
