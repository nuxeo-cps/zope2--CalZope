# -*- coding: ISO-8859-15 -*-
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
# $Id: calendartest.py 24686 2005-07-06 16:05:28Z lregebro $
"""
  CPSSharedCalendar Functional Tests
"""

import unittest, base64, sys
from datetime import datetime, timedelta

import transaction
import zLOG
from StringIO import StringIO
from ZPublisher.Response import Response
from ZPublisher.Request import Request
from ZPublisher.Test import publish_module
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from Testing.ZopeTestCase import FunctionalTestCase, installProduct
from Testing.ZopeTestCase import folder_name, user_role, standard_permissions
from Testing.ZopeTestCase.functional import ResponseWrapper
from zope.app import zapi

installProduct('CalCore')
installProduct('Five')
installProduct('CalZope')

from Products.Five import zcml
from Products.Five.zcml import load_config
from Products.Five.site.interfaces import IFiveUtilityRegistry
from Products.Five.site.localsite import enableLocalSiteHook
from Products.Five.tests.testing.folder import manage_addFiveTraversableFolder

from calcore.interfaces import IAttendeeSource, IStorageManager
from Products.CalZope.interfaces import IZopeAttendeeSource
from Products.CalZope.zopecal import UserFolderAttendeeSource, StorageManager

import Products.CalZope

load_config('configure.zcml', package=Products.CalZope)
load_config('overrides.zcml', package=Products.CalZope)

manager_id = 'manager'
user_id = 'user'


class CalendarTestCase(FunctionalTestCase):

    # Some useful constants
    add_product_path = 'manage_addProduct/CPSSharedCalendar'
    calendar_name = 'calendar'
    event_name = 'event'

    def getTraceback(self, response):
        return getattr(response._response, '_text_traceback', None)

    def assertResponse(self, response, status, message=''):
        if isinstance(status, int):
            status = [status]
        if not response.getStatus() in status:
            tb = self.getTraceback(response)
            if tb is not None:
                raise self.failureException, tb
            else:
                raise ValueError, "Response had status %s, expected %s. %s" % (
                    response.getStatus(), status, message)

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

        sm = StorageManager('IStorageManager', 'IStorageManager')
        IFiveUtilityRegistry(self.folder).registerUtility(IStorageManager, sm)
        asrc = UserFolderAttendeeSource()
        IFiveUtilityRegistry(self.folder).registerUtility(IZopeAttendeeSource, asrc)
        IFiveUtilityRegistry(self.folder).registerUtility(IAttendeeSource, asrc)

        self.folder.acl_users._doAddUser(
            manager_id, 'secret', ['Manager'], [])
        self.folder.acl_users._doAddUser(
            user_id, 'secret', [], [])

        # Set up standard permissions:
        from Products.CalZope.permissions import permissions
        for permission, roles in permissions.items():
            pms = self.folder.rolesOfPermission(permission)
            p_roles = [r['name'] for r in pms if r['selected']]
            for role in roles:
                if role not in p_roles:
                    p_roles.append(role)
            self.folder.manage_permission(permission, p_roles, 1)

        # Create two "home calendars"
        self.folder.manage_addProduct['CalZope'].manage_addCalendar(
            'manager_cal', 'Managers Calendar')
        manager_attendee = asrc.getAttendee(manager_id)
        self.folder.manager_cal.addAttendee(manager_attendee)
        self.folder.manager_cal.manage_addLocalRoles(manager_id, ['Owner'])
        self.managercalpath = '/'.join(self.folder.manager_cal.getPhysicalPath())

        self.folder.manage_addProduct['CalZope'].manage_addCalendar(
            'user_cal', 'Users Calendar')
        user_attendee = asrc.getAttendee(user_id)
        self.folder.user_cal.addAttendee(user_attendee)
        self.folder.user_cal.manage_addLocalRoles(user_id, ['Owner'])
        self.usercalpath = '/'.join(self.folder.user_cal.getPhysicalPath())

    def print_log_errors(self, min_severity=zLOG.INFO):
        if hasattr(zLOG, 'old_log_write'):
            return
        def log_write(subsystem, severity, summary, detail, error,
                      PROBLEM=zLOG.PROBLEM, min_severity=min_severity):
            if severity >= min_severity:
                print "%s(%s): %s, %s" % (subsystem, severity, summary, detail)
        zLOG.old_log_write = zLOG.log_write
        zLOG.log_write = log_write
    
    def ignore_log_errors(self):
        if hasattr(zLOG, 'old_log_write'):
            zLOG.log_write = zLOG.old_log_write
            del zLOG.old_log_write
    
    def publish(self, path, basic=None, env=None, extra=None, request_method='GET', stdin=None):
        try:
            import Zope2
            return self.publish28(path, basic, env, extra, request_method, stdin)
        except ImportError:
            #Zope 2.7
            return FunctionalTestCase.publish(self, path, basic, env, extra, request_method, stdin)
        
    def publish28(self, path, basic=None, env=None, extra=None, request_method='GET', stdin=None):
        '''Publishes the object at 'path' returning a response object.'''

        # Save current security manager
        sm = getSecurityManager()

        # Commit the sandbox for good measure
        transaction.commit()

        if env is None:
            env = {}
        if extra is None:
            extra = {}

        request = self.app.REQUEST

        env['SERVER_NAME'] = request['SERVER_NAME']
        env['SERVER_PORT'] = request['SERVER_PORT']
        env['REQUEST_METHOD'] = request_method

        p = path.split('?')
        if len(p) == 1:
            env['PATH_INFO'] = p[0]
        elif len(p) == 2:
            [env['PATH_INFO'], env['QUERY_STRING']] = p
        else:
            raise TypeError, ''

        if basic:
            env['HTTP_AUTHORIZATION'] = "Basic %s" % base64.encodestring(basic)

        if stdin is None:
            stdin = StringIO()

        outstream = StringIO()
        response = Response(stdout=outstream, stderr=sys.stderr)
        
        # In Zope 2.8 these seems to have to sit directly on the request or
        # Five will not find them.
        request=Request(stdin, env, response)
        for k,v in extra.items():
            setattr(request, k, v)

        publish_module('Zope2', response=response, stdin=stdin, environ=env, request=request)

        # Restore security manager
        setSecurityManager(sm)

        return ResponseWrapper(response, outstream, path)
