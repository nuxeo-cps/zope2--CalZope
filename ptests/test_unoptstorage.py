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
# $Id: test_navigation.py 24820 2005-07-12 11:13:31Z lregebro $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from performancetest import BasePerformanceTest
from calcore import cal

from OFS.SimpleItem import SimpleItem
from BTrees.OOBTree import OOBTree
from Products.CalZope.storage import ZODBEvent

class UnoptimizedStorage(SimpleItem, cal.StorageBase):
    """Minimalistic, non-optimized version of ZODB storage.
    
    Temporarily Saved here because we need to test upgrading from this to
    the new ZODB storage. //regebro
    """
    def _initEvents(self):
        return OOBTree()

    def _eventFactory(self, event_id, spec):
        return ZODBEvent(event_id, spec)

    def indexEvent(self, unique_id, event):
        pass
    
    reindexEvent = indexEvent
    
    def unindexEvent(event):
        pass
    
class TestUnoptStorage(BasePerformanceTest):
    
    def setUpStorage(self):
        print "Unoptimized ZODBStorage"
        storagemanager = self.folder.portal_calendar.storage_manager
        storagemanager.setStorage(UnoptimizedStorage('unoptstorage'))
    
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestUnoptStorage),
        ))

if __name__ == '__main__':
    # Standard:
    unittest.main(defaultTest='test_suite')
    
    #Profiling:
    #import profile, pstats
    #profile.run("unittest.main(defaultTest='test_suite')", 'profile.stats')
    #p = pstats.Stats('profile.stats')
    #p.strip_dirs()
    #p.sort_stats('time', 'module')
    #p.print_stats()
