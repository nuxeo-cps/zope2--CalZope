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

icalsimple = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20051020T095500Z
DTEND:20051020T105500Z
UID:simpleevent
DESCRIPTION:Description.
SUMMARY:A simple event.
CLASS:PUBLIC
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""

icalcomplex = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20051020T095500Z
DTEND:20051020T105500Z
UID:complexevent
DESCRIPTION:This is an event that has loads of features, but all still in p
 lain text. This should be handled easily, or there is a bug in the icalend
 ar library.
SUMMARY:A complex, plain text, event.
LOCATION:In a test runner.
CATEGORIES:this,is,a,list,of,categories
CLASS:PUBLIC
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""

icalunicode = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20051020T095500Z
DTEND:20051020T105500Z
UID:unicodeevent
DESCRIPTION:This is an \xc3\xa9v\xc3\xa8nt that has loads of fe\xc3\xa4ture
 s, but all in uni\xc3\xa7ode. This should be h\xc3\xa5ndled and c\xc3\xb6n
 verted by CalZope, so that strings with ISO-8559-15 code is used. Jour d
 e l\xe2\x80\x99an. Double bar: \xe2\x80\x96.
SUMMARY:A \xc3\xa7\xc3\xb6mplex, unic\xc3\xb6de, \xc3\xa9vent.
LOCATION:In a t\xc3\xabst r\xc3\xbcnner.
CATEGORIES:this,is,\xc3\xa4,list,\xc3\xb6f,\xc3\xa7at\xc3\xa9gories
CLASS:PUBLIC
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""

class TestiCalendar(CalendarTestCase):
    
    def afterSetUp(self):
        CalendarTestCase.afterSetUp(self)

        self.folder.acl_users._doAddUser('martijn', 'martijn', ['Manager'], [])
        self.folder.manage_addProduct['CalZope'].manage_addCalendar(
            'martijn_cal', 'Martijns Calendar')
        source = zapi.getUtility(IZopeAttendeeSource, context=self.folder)
        calendar = self.folder.martijn_cal
        calendar.addAttendee(source.getAttendee('martijn'))
        
    def test_simpleImport(self):
        calendar = self.folder.martijn_cal
        calendar.import_(icalsimple)
        event = calendar.getEvent('simpleevent')
        self.failUnlessEqual(event.title, 'A simple event.')

    def test_complexImport(self):
        calendar = self.folder.martijn_cal
        calendar.import_(icalcomplex)
        event = calendar.getEvent('complexevent')
        self.failUnlessEqual(event.title, 'A complex, plain text, event.')
        self.failUnlessEqual(event.description, 
            'This is an event that has loads of features, but all still in '
            'plain text. This should be handled easily, or there is a bug in '
            'the icalendar library.')
        self.failUnlessEqual(event.location, 'In a test runner.')
        catlist = ['this','is','a','list','of','categories']
        for cat in catlist:
            self.failUnless(cat in event.categories)
        for cat in event.categories:
            self.failUnless(cat in catlist)

    def test_unicodeImport(self):
        calendar = self.folder.martijn_cal
        calendar.import_(icalunicode)
        event = calendar.getEvent('unicodeevent')
        self.failUnlessEqual(event.title, 'A ��mplex, unic�de, �vent.')
        self.failUnlessEqual(event.description, 
            'This is an �v�nt that has loads of fe�tures, but all in uni�ode. '
            'This should be h�ndled and c�nverted by CalZope, so that strings '
            'with ISO-8559-15 code is used. '
            "Jour de l'an. Double bar: &#8214;.")
        self.failUnlessEqual(event.location, 'In a t�st r�nner.')
        catlist = ['this','is','�','list','�f','�at�gories']
        for cat in catlist:
            self.failUnless(cat in event.categories, 
                'Expected category %s missing. Found %s' % (
                    cat, str(event.categories)))
        for cat in event.categories:
            self.failUnless(cat in catlist, 
                'Category %s unexpected' % cat)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestiCalendar),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
