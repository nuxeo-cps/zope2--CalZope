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
from Testing.ZopeTestCase import ZopeTestCase, installProduct
from Testing.ZopeTestCase import folder_name, user_role, standard_permissions

from Products.Five import zcml
from Products.Five.tests.testing.folder import manage_addFiveTraversableFolder
from Products.Five.site.interfaces import IFiveUtilityRegistry
from Products.Five.site.localsite import enableLocalSiteHook
from zope.app.component.hooks import setSite

installProduct('CalCore')
installProduct('CalZope')
installProduct('Five')

from calcore.interfaces import IStorageManager, IAttendeeSource
from Products.CalZope.interfaces import IZopeAttendeeSource, IZopeStorageManager
from Products.CalZope.zopecal import UserFolderAttendeeSource, StorageManager

class CalendarTestCase(ZopeTestCase):
    
    def _setupFolder(self):
        '''Creates and configures the folder.'''
        manage_addFiveTraversableFolder(self.app, folder_name)
        self.folder = getattr(self.app, folder_name)
        self.folder._addRole(user_role)
        self.folder.manage_role(user_role, standard_permissions)

    def afterSetUp(self):
        zcml.load_string(
"""<configure xmlns="http://namespaces.zope.org/zope"
           xmlns:five="http://namespaces.zope.org/five">
 <five:localsite class="Products.Five.tests.testing.folder.FiveTraversableFolder" />
</configure>""")
        enableLocalSiteHook(self.folder)

        sm = StorageManager('IZopeStorageManager', 'IZopeStorageManager')
        # In Five 1.3 you need to register every utility for all interfaces
        # used. This will go away in Five 1.5, where you can just register
        # the topmost interface.
        IFiveUtilityRegistry(self.folder).registerUtility(IZopeStorageManager, sm)
        IFiveUtilityRegistry(self.folder).registerUtility(IStorageManager, sm)
        asrc = UserFolderAttendeeSource()
        IFiveUtilityRegistry(self.folder).registerUtility(IZopeAttendeeSource, asrc)
        IFiveUtilityRegistry(self.folder).registerUtility(IAttendeeSource, asrc)
        setSite(self.folder)
        