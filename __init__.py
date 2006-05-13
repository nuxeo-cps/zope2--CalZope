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
# $Id$

def initialize(context):
    import zopecal

    context.registerClass(
        zopecal.CalendarTool,
        constructors = (zopecal.manage_addCalendarTool,
                        zopecal.manage_addCalendarTool),
        )


    context.registerClass(
        zopecal.StorageManager,
        constructors = (zopecal.manage_addStorageManagerForm,
                        zopecal.manage_addStorageManager),
        )


    context.registerClass(
        zopecal.UserFolderAttendeeSource,
        constructors = (zopecal.manage_addUserFolderAttendeeSourceForm,
                        zopecal.manage_addUserFolderAttendeeSource),
        )
    
    context.registerClass(
        zopecal.Calendar,
        constructors = (zopecal.manage_addCalendarForm,
                        zopecal.manage_addCalendar),
        )

    from permissions import setDefaultRoles, permissions
    for permission, roles in permissions.items():
        setDefaultRoles(permission, roles)
