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
# $Id$

# This ought to be in AccessControl.SecurityInfo. But it isn't.
# So I copied it from CMFCore.
import Products
from AccessControl.Permission import _registeredPermissions
from AccessControl.Permission import pname
from Globals import ApplicationDefaultPermissions

def setDefaultRoles(permission, roles):
    '''
    Sets the defaults roles for a permission.
    '''
    registered = _registeredPermissions
    if not registered.has_key(permission):
        registered[permission] = 1
        Products.__ac_permissions__=(
            Products.__ac_permissions__+((permission,(),roles),))
        mangled = pname(permission)
        setattr(ApplicationDefaultPermissions, mangled, roles)


# Sensible defaults for most permissions
permissions = {
    # Attendee/Calendar level permissions:
    
    # The right to view an attendees calendar and its public events.
    # Often everybody in a company should be able to see everybody's
    # Calendar, and then Authenticated could have this permission.
    # This more restrictive set is the minimal reasonable set.
    'View calendar': ['Manager', 'Owner', 'AttendeeManager', 'AttendeeReader'],
    'Edit calendar': ['Manager', 'Owner', 'AttendeeManager'],
    # This permission controls the possibility to create an event 
    # as that attendee, that is, create meetings where the attendee is the
    # organizer/chair, or non-meeting events for this attendee.
    'Create events': ['Manager', 'Owner', 'AttendeeManager'],
    # Normally, anybody has the right to invite anybody
    'Invite attendee': ['Manager', 'Authenticated'],
    # This is the permission to manage one's attendees participation status
    'Manage participation status': ['Manager', 'Owner', 'AttendeeManager'],
    
    # Event level permissions:

    # The right to view an event. If you don't have this permission
    # the event will be rendered as busy, but without further details.
    'View public event': ['Manager', 'EventParticipant', 'AttendeeReader'],
    # The right to view a private event. 
    'View private event': ['Manager', 'EventParticipant'],
    # Only the organizer can modify and delete an event by default
    'Modify event': ['Manager', 'EventOrganizer'],
    'Delete event': ['Manager', 'EventOrganizer'],
    # This is the right to invite more people to an event
    # It does *not* affect the right to delegate an invitation. Instead,
    # You can delegate one persons invitation to another person if you have
    # the 'Manage participation status' for the invited person, and 
    # 'Invite attendee' for the one you delegate to.
    'Invite attendees': ['Manager', 'EventOrganizer', 'EventParticipant'],
    # This allows you to set the status for other people on an event.
    'Manage attendees': ['Manager', 'EventOrganizer'],
    }
