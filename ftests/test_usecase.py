# -*- coding: iso-8859-15 -*-
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
from datetime import datetime, timedelta
from calendartest import CalendarTestCase, user_id, manager_id

class testUseCase(CalendarTestCase):

    def afterSetUp(self):
        CalendarTestCase.afterSetUp(self)

        # Create use case users and calendars
        asrc = self.folder.utilities.IZopeAttendeeSource
        for uid in ('florent', 'martijn', 'bob'):
            self.folder.acl_users._doAddUser(
                uid, 'secret', [], [])

            self.folder.manage_addProduct['CalZope'].manage_addCalendar(
                uid, '%s Calendar' % uid)
            attendee = asrc.getAttendee(uid)
            self.folder[uid].addAttendee(attendee)
            self.folder[uid].manage_addLocalRoles(uid, ['Owner'])

        self.folderpath = '/'.join(self.folder.getPhysicalPath())

    
    def test_usecase(self):
        """Go through the use case, but this time with a user interface,
        and without the room. CalZope doesn't support resource attendees.
        """

        # Now Florent will create a tentative event for a meeting tomorrow,
        # at 4 pm, lasting an hour::
        date = datetime.now() + timedelta(1)
        year = date.year
        month = date.month
        day = date.day
        
        response = self.publish(
            self.folderpath + '/florent/+/addevent.html',
            basic='florent:secret',
            extra={'form': {'field.dtstart': '%s/%s/%s' % (month, day, year),
                            'field.dtstart_hour': '16',
                            'field.dtstart_minute': '00',
                            'field.dtend': '%s/%s/%s' % (month, day, year),
                            'field.dtend_hour': '17',
                            'field.dtend_minute': '00',
                            'field.title': "Florent's Meeting",
                            'field.status': 'TENTATIVE',
                            'field.access': 'PUBLIC',
                            'UPDATE_SUBMIT': 'Add'},
                    'SESSION': {},})
        self.assertResponse(response, 302) # This add form redirects if it works
        
        event_id = self.folder.florent.getEvents((
            datetime(year, month ,01), datetime(year, month, 01)+timedelta(32)
            ))[0].getId()
        
        # When Florent now checks his events, he'll see the meeting::
        response = self.publish(
            '%s/florent/%s/%s' % (self.folderpath, year, month),
            basic='florent:secret',
            extra={'SESSION':{}})
        self.assertResponse(response, 200)
        self.assert_("Florent's Meeting" in response.getBody(),
                         'Event not found in month-view')

        # Since he's the organizer, he has automatically accepted the event::
        response = self.publish(
            '%s/florent/event/%s' % (self.folderpath, event_id),
            basic='florent:secret')
        self.assert_("Accepted" in response.getBody(), 'Event not accepted')
  
        # Martijn, Bob and Room 1 are still not invited::
        for uid in ('martijn', 'bob'):
            response = self.publish(
                '%s/%s/%s/%s' % (self.folderpath, uid, year, month),
                basic='%s:secret' % uid,
                extra={'SESSION':{}})
            self.assertResponse(response, 200)
            self.assert_("Florent's Meeting" not in response.getBody(), 
                         'Event found in month-view although not invited')

        # Now Florent invites Martijn and Bob::
        response = self.publish(
                '%s/florent/event/%s/attendees.html' % (
                    self.folderpath, event_id),
                basic='florent:secret',
                extra={'form': {'add_martijn':'on',
                                'add_bob':'on',
                                'UPDATE_ADD': 'Add'},
                       'SESSION':{}})

        self.assertResponse(response, 200)

        # All these attendees will now see the event too::
        for uid in ('martijn', 'bob'):
            response = self.publish(
                '%s/%s/%s/%s' % (self.folderpath, uid, year, month),
                basic='%s:secret' % uid,
                extra={'SESSION':{}})
            self.assertResponse(response, 200)
            self.assert_("Florent's Meeting" in response.getBody(), 
                         'Event not found in month-view although invited')
        
        # The status for Martijn and Bob will be 'NEEDS-ACTION'::

        for uid in ('martijn', 'bob'):
            response = self.publish(
                '%s/%s/event/%s' % (self.folderpath, uid, event_id),
                basic='%s:secret' % uid) 
            self.assertResponse(response, 200)
            self.assert_("Needs Action" in response.getBody(), 
                         'Wrong status')
  
        # Martijn will now see that there action items::
        response = self.publish(
            '%s/martijn/action_needed_events.html' % self.folderpath,
            basic='%s:secret' % 'martijn')
        self.assertResponse(response, 200)
        self.assert_("Florent's Meeting" in response.getBody(), 
                     'Event not listed')
        self.assert_("Needs Action" in response.getBody(), 
                     'Wrong status')

        # He accepts it::
        response = self.publish(
            '%s/martijn/action_needed_events.html' % self.folderpath,
            basic='%s:secret' % 'martijn',
            extra={'form': {'participation_status':'ACCEPTED',
                            'event_ids': [event_id],
                            'update_participation_status': 'Change'}}) 

        # There are no more action items for Martijn::

        self.assert_("No events." in response.getBody(), 
                     "Could not accept event")

        # Florent can try to reinvite Martijn, but Martijn will remain accepted::

        response = self.publish(
                '%s/florent/event/%s/attendees.html' % (
                    self.folderpath, event_id),
                basic='florent:secret',
                extra={'form': {'add_martijn':'on',
                                'UPDATE_ADD': 'Add'}}) 
        self.assertResponse(response, 200)

        response = self.publish(
            '%s/%s/event/%s' % (self.folderpath, 'martijn', event_id),
            basic='%s:secret' % uid) 
        self.assertResponse(response, 200)
        self.assert_("Accepted" in response.getBody(), 
                     'Status changed on reinvite.')
  
        # Florent can get a list of all events he is the organizer of::
        response = self.publish(
            '%s/florent/organized_events.html' % self.folderpath,
            basic='%s:secret' % 'florent')
        self.assertResponse(response, 200)
        self.assert_("Florent's Meeting" in response.getBody(), 
                     'Event not listed')

        # Florent decides in the end it was all a mistake, and the event is removed::

        response = self.publish(
            '%s/florent/event/%s/delete.html' % (self.folderpath, event_id),
            basic='%s:secret' % 'florent')
        self.assertResponse(response, 200)
        response = self.publish(
            '%s/florent/event/%s/delete.html' % (self.folderpath, event_id),
            basic='%s:secret' % 'florent',
            extra={'form': {'SUBMIT_DELETE': 'Delete'}}) 
        self.assertResponse(response, 302)

        for uid in ('florent', 'martijn', 'bob'):
            response = self.publish(
                '%s/%s/%s/%s' % (self.folderpath, uid, year, month),
                basic='%s:secret' % uid,
                extra={'SESSION':{}})
            self.assertResponse(response, 200)
            self.assert_("Florent's Meeting" not in response.getBody(), 
                         'Deleted event shows up.')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(testUseCase),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
