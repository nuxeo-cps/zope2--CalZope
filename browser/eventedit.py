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

from datetime import datetime, time, timedelta
combine = datetime.combine

from AccessControl import Unauthorized
from zope.interface import implements
from zope.app import zapi
from zope.event import notify

from Products.CalZope.browser.interfaces import IEventEditSchema
from calcore.interfaces import IStorageManager
from calcore.events import EventModifiedEvent

class EventEdit(object):
    """An adapter used to present a different edit form for events.

    This adapter is actually mostly a decorator of the underlying object,
    but adds a different dtend field that is specified in a different schema.
    """
    implements(IEventEditSchema)
    
    def __init__(self, context):
        self.__dict__['context'] = context

    # whenever we need an attribute we don't have, go to the context
    def __getattr__(self, name):
        return getattr(self.__dict__['context'], name)

    # set to context too, except for things we define as properties
    def __setattr__(self, name, value):
        if hasattr(getattr(self.__class__, name, None), '__set__'):
            object.__setattr__(self, name, value)
        else:
            setattr(self.__dict__['context'], name, value)

    # new dtend property
    def _get_dtend(self):
        context = self.__dict__['context']
        result = context.dtstart + context.duration
        # All day events should be shown ending at 23:55 the last day,
        # and not 00:00 the day after.
        if context.allday:
            result -= timedelta(minutes=5)
        return result
    
    def _set_dtend(self, value):
        context = self.__dict__['context']
        context.duration = value - context.dtstart

    dtend = property(_get_dtend, _set_dtend)

from zope.app.form.utility import getWidgetsData
from Products.Five.form import EditView

class EventEditSaver:
    """This makes sure that when an event is edited, allday is taking
    into account.
    """
       
    def _setUpWidgets(self):
        EditView._setUpWidgets(self)
        self.title_widget.displayWidth = 50
        self.description_widget.width = 48
        self.description_widget.height = 7
        self.location_widget.width = 30
        self.location_widget.height = 7
        self.categories_widget.width = 30
        self.categories_widget.height = 7
        
    def changed(self):
        # if we have negative duration (should not happen unless you 
        # override the end datetime widget)
        if self.context.duration < timedelta(days=0):
            self.context.duration = timedelta(hours=1)
            self.dtend_widget.setRenderedValue(
                self.context.dtstart +
                self.context.duration)
            
        if self.context.allday:
            self.context.alldayAdjust()
            # also modify the widgets so form displays changed info
            # properly
            self.dtstart_widget.setRenderedValue(self.context.dtstart)
            # substract five minutes from duration again for display
            self.dtend_widget.setRenderedValue(
                self.context.dtstart +
                self.context.duration - timedelta(minutes=5))
        
        notify(EventModifiedEvent(self.context))
        
