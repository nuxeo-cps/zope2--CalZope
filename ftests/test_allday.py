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

class testAccessControl(CalendarTestCase):
    
    def test_alldayCreate(self):
        # The time should not make any kind of difference
        response = self.publish(
            '%s/+/addevent.html' % self.usercalpath,
            basic='%s:secret' % user_id,
            extra={'form': {'field.dtstart': '04/01/2005',
                            'field.dtstart_hour': '10',
                            'field.dtstart_minute': '30',
                            'field.dtend': '04/01/2005',
                            'field.dtend_hour': '10',
                            'field.dtend_minute': '30',
                            'field.title': 'testevent',
                            'field.status': 'CONFIRMED',
                            'field.access': 'PRIVATE',
                            'field.allday': 'on',
                            'field.allday.used': '',
                            'UPDATE_SUBMIT': 'Add'},
                    'SESSION': {}})
        self.assertResponse(response, 302) # This add form redirects if it works
        
        events = self.folder.user_cal.getEvents(
            (datetime(2005,04,01), datetime(2005,04,02)))
        self.failUnlessEqual(len(events), 1)
        event = events[0]
        self.failUnlessEqual(event.dtstart, datetime(2005, 4, 1, 0, 0))
        self.failUnlessEqual(event.duration, timedelta(1))
        event_id = event.getId()
        
        response = self.publish(
            '%s/event/%s/edit.html' % (self.usercalpath, event_id),
            basic='%s:secret' % user_id)
        self.assertResponse(response, 200)
        body = response.getBody()

        # Make sure the start date and end date fields are correctly displayed.
        # The should be displayed as starting at 00:00 the start day, and 
        # ending at 23:55 the last day, even though it really is stored
        # as 00:00 the day after the next day.
        datefield = '<input class="textType" id="field.%(field)s" ' \
                    'name="field.%(field)s"'
        self.failUnless(body.find(datefield % {'field': 'dtstart'}) != -1)
        self.failUnless(body.find(datefield % {'field': 'dtend'}) != -1)

        fieldstart = '<select id="field.%(field)s" name="field.%(field)s">'
        fieldselect = '<option selected="selected" value="%(val)s">'
        for field, val in [('dtstart_hour', '00'),
                           ('dtstart_minute', '00'),
                           ('dtend_hour', '23'),
                           ('dtend_minute', '55')]:
            beginpos = body.find(fieldstart % {'field': field})
            teststr = body[beginpos:]
            fieldval = fieldselect % {'val': val}
            self.failUnless(teststr.find(fieldval) != -1, 'Did not find ' + teststr)
                

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(testAccessControl),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
