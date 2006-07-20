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
# $Id: install.py 30261 2005-12-04 14:03:51Z lregebro $

from zope.app.components.interfaces import ISite
from zope.app import zapi

from AccessControl import getSecurityManager
from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod

import Products.Five
from Products.Five import zcml
from Products.Five.site.interfaces import IFiveUtilityRegistry
from Products.Five.site.localsite import enableLocalSiteHook
from Products.Five.site.tests.dummy import manage_addDummySite

from calcore.interfaces import IAttendeeSource, IStorageManager
from Products.CalZope.permissions import permissions as cal_permissions
from Products.CalZope.interfaces import IZopeAttendeeSource

from Products.CalZope.zopecal import StorageManager, UserFolderAttendeeSource


def install(self):
    if not 'calendars' in self.objectIds():
        zcml.load_config("meta.zcml", Products.Five)
        zcml.load_config("permissions.zcml", Products.Five)
        zcml.load_config("configure.zcml", Products.Five.site)
        zcml_text = """\
        <five:localsite
            xmlns:five="http://namespaces.zope.org/five"
            class="Products.Five.site.tests.dummy.DummySite" />"""
        zcml.load_string(zcml_text)  
        manage_addDummySite(self, 'calendars')
        
    site = self['calendars']
    if not ISite.providedBy(site):
        enableLocalSiteHook(site)
    
    # Create tools
    try:
        sm = StorageManager()
        IFiveUtilityRegistry(site).registerUtility(IStorageManager, sm)
    except ValueError:
        pass
    
    asrc = UserFolderAttendeeSource()
    try:
        IFiveUtilityRegistry(site).registerUtility(IAttendeeSource, asrc)
    except ValueError:
        pass
    try:
        IFiveUtilityRegistry(site).registerUtility(IZopeAttendeeSource, asrc)
    except ValueError:
        pass

    if not 'create_home_calendar' in site.objectIds():
        manage_addExternalMethod(site, 'create_home_calendar', 
                                 'Create Home Calendar', 'CalZope.install',
                                 'create_home_calendar')

    # Set up standard permissions:
    from Products.CalZope.permissions import permissions
    for permission, roles in permissions.items():
        pms = self.rolesOfPermission(permission)
        p_roles = [r['name'] for r in pms if r['selected']]
        for role in roles:
            if role not in p_roles:
                p_roles.append(role)
        self.manage_permission(permission, p_roles, 1)

    return "Install done!"


def create_home_calendar(self):
    # Create "home calendar" for current user
    asrc = zapi.getUtility(IAttendeeSource)
    userid = getSecurityManager().getUser().getId()
    
    calendar_id = '%s_cal' % userid
    self.manage_addProduct['CalZope'].manage_addCalendar(
        calendar_id, 'Calendar for %s' % userid)
    cal = self[calendar_id]
    attendee = asrc.getAttendee(userid)
    cal.addAttendee(attendee)
    cal.manage_addLocalRoles(userid, ['Owner'])

    return "Done!"
