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

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from performancetest import BasePerformanceTest
from calcore import cal

class TestMemoryStorage(BasePerformanceTest):
    
    def setUpStorage(self):
        storagemanager = zapi.getUtility(IStorageManager, context=self.folder)
        storagemanager.setStorage(cal.MemoryStorage('memorystorage'))
        print "Unoptimized MemoryStorage"
    
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestMemoryStorage),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
