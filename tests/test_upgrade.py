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

# a duplication from usecase.txt in CalCore,
# but hard to reuse doctests in Zope 2 context..
import unittest
from datetime import datetime, timedelta

from zope.app import zapi

from calendartest import CalendarTestCase
from calcore import cal, recurrent
from calcore.interfaces import IStorageManager
from Products.CalZope.interfaces import IZopeAttendeeSource
from Products.CalZope.storage import ZopeEventSpecification

class TestUpgrade(CalendarTestCase):
            
    def test_upgrade(self):
        storage = zapi.getUtility(IStorageManager, context=self.folder)
        # Create a bunch of events:
        for i in range(1,31):
            dtstart = datetime(2006,7,i,10,0)
            duration = timedelta(minutes=60)
            spec = {'dtstart': dtstart, 
                    'duration': duration,
                    'title': 'Thïs évènt hàs mäñÿ çhåráctêrs',
                    'description': 'Thé dèscrïption àlsö.',
                    'location': 'Löcätion',
                    'status': 'TENTATIVE',
                    'organizer': None,
                    'recurrence': None,
                    'allday': False,
                    'categories': None,
                    'transparent': False,
                    'access': 'PUBLIC',
                    'document': '',
                }
            storage.createEvent(**spec)

        storage._storage._upgrade2unicode()

        for event in storage.getEvents((None, None)):
            self.failUnless(event.title, u'Th\xefs \xe9v\xe8nt h\xe0s '
                            u'm\xe4\xf1\xff \xe7h\xe5r\xe1ct\xears')
            self.failUnless(event.description, 
                            u'Th\xe9 d\xe8scr\xefption \xe0ls\xf6.')
            self.failUnless(event.location, u'L\xf6ca\xe4tion')
            

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestUpgrade),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
