# -*- coding: iso-8859-15 -*-
#
# The code for DivDatetimeWidget, DivDateWidget and supporting methds is ZPL. 
# It's based on code by Gary Poster, gary@zope.com and then extended a lot.
# We have been given permission by Gary Poster to include it in this product.
#
# The rest of the code is:
#
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

from time import strptime
from datetime import time, timedelta, datetime, date
from zope.app.form.browser import DatetimeWidget, DateWidget, TextWidget
from zope.app.form.browser.widget import renderElement
from zope.app.form.browser.itemswidgets import TranslationHook
from zope.app.datetimeutils import DateTimeError
from zope.app.datetimeutils import tzinfo, parseDatetimetz
from zope.app.form.interfaces import ConversionError, WidgetInputError
from zope.app.form.interfaces import InputErrors
from zope.schema.interfaces import ValidationError

from Products.CalZope.interfaces import IBusyChecker

from zope.i18nmessageid import MessageFactory
_ = MessageFactory("calendar")

from zope.i18n.interfaces import IUserPreferredLanguages, ILanguageAvailability
# List of the supported languages for the jscalendar.
# These must be synced with what is configured in the configure.zcml.
supported_languages = ('en', 'de', 'es', 'fr', 'it', 'nl', 'pt-br', 'ro',)

def setupLanguage(context, request):
    if getattr(request, 'jscalendar_language', None) is not None:
        # Only do this once per request
        return
    user_langs = IUserPreferredLanguages(request).getPreferredLanguages()
    site_lang_adapter = ILanguageAvailability(context, None)
    if site_lang_adapter is not None:
        site_langs = site_lang_adapter.getAvailableLanguages()
        # Filter out languages not supported by jscalendar:
        site_langs = [l for l in site_langs if l in supported_languages]
    else:
        site_langs = supported_languages
    
    use_lang = None
    for lang in user_langs:
        if lang in site_langs:
            use_lang = lang
            break
    if use_lang is None:
        use_lang = site_langs[0]

    request.jscalendar_language = use_lang
    

class TimedeltaWidget(TextWidget):

    displayWidth = 10

    def _toFormValue(self, value):
        value = super(TimedeltaWidget, self)._toFormValue(value)
        if value:
            duration = (value.days * 86400) + value.seconds
            hours = duration / 3600
            minutes = (duration % 3600) / 60
            value = '%02d:%02d'% (hours, minutes)
        return value

    def _toFieldValue(self, input):
        if input == self._missing:
            return self.context.missing_value
        else:
            try:
                hours, minutes = input.split(':')
                return timedelta(hours=int(hours), minutes=int(minutes))
            except (DateTimeError, ValueError, IndexError), v:
                raise ConversionError("Invalid duration", v)

    def _getDefault(self):
        # Get this from the field instead
        return timedelta(hours=1)

# This should probably be very refactored. Maybe we should use
# sequence widgets, and separate the date and time into separate
# fields?

class DivDatetimeWidget(TranslationHook, DatetimeWidget):
    # NOTE: presentation is only good for non-tzinfo-aware datetimes.

    time_format = '%Y-%m-%d'
    displayWidth = 10

    def _unconvert(self, value):
        if value == self.context.missing_value:
            return self._missing
        elif isinstance(value, datetime):
            format = self.translate(_(self.time_format))
            return value.strftime(str(format))
        else:
            return str(value)

    def __call__(self):
        setupLanguage(self.context.context, self.request)
        value = self._getFormValue()
        if value:
            if isinstance(value, datetime):
                datestr = value.strftime(str(self.translate(_(self.time_format))))
                hour = value.hour
                minute = value.minute
            else:
                datestr = str(value)
                hour = int(self.request.form.get(self.name + '_hour', 0))
                minute = int(self.request.form.get(self.name + '_minute', 0))
        else:
            datestr = ''
            hour = int(self.request.form.get(self.name + '_hour', 0))
            minute = int(self.request.form.get(self.name + '_minute', 0))
        res = renderElement(self.tag,
                            type=self.type,
                            name=self.name,
                            id=self.name,
                            value=datestr,
                            cssClass=self.cssClass,
                            style=self.style,
                            size=self.displayWidth,
                            extra=self.extra,
                            title=self.translate(_('YYYY-MM-DD')))
        calendar_res = make_calendar_widget(
            self.request,
            "%s_launch_img" % self.name,
            self.name,
            self.translate(_(self.time_format)),
            False, title=self.translate(_('Date selector')))
        hour_res = _makeHourDropDown(self.name + '_hour', selected=hour)
        minute_res = _makeMinuteDropDown(self.name + '_minute', selected=minute)
        return "\n".join([res, calendar_res, hour_res,minute_res])

    def hasInput(self):
        for ext in ('', '_hour', '_minute'):
            if not self.name + ext in self.request.form:
                return False
        return True

    def _getFormInput(self):
        return self.request.form[self.name] + ' ' + \
               self.request.form[self.name + '_hour'] + ':' + \
               self.request.form[self.name + '_minute']

    def _toFieldValue(self, input):
        if input == self._missing:
            return self.context.missing_value
        else:
            try:
                format = self.translate(_(self.time_format))  + ' %H:%M'
                return str2datetime(input, format)
            except (DateTimeError, ValueError, IndexError), v:
                raise ConversionError("Invalid datetime data", v)

class DivDateWidget(TranslationHook, DateWidget):

    time_format = '%Y-%m-%d'
    displayWidth = 10

    def _unconvert(self, value):
        if value == self.context.missing_value:
            return self._missing
        elif isinstance(value, date):
            format = self.translate(_(self.time_format))
            return value.strftime(str(format))
        else:
            return str(value)

    def __call__(self):
        setupLanguage(self.context.context, self.request)
        value = self._getFormValue()
        if value and isinstance(value, date):
            datestr = value.strftime(str(self.translate(_(self.time_format))))
        else:
            datestr = ''
        res = renderElement(self.tag,
                            type=self.type,
                            name=self.name,
                            id=self.name,
                            value=datestr,
                            cssClass=self.cssClass,
                            style=self.style,
                            size=self.displayWidth,
                            extra=self.extra,
                            title=self.translate(_('YYYY-MM-DD')))
        calendar_res = make_calendar_widget(
            self.request,
            "%s_launch_img" % self.name,
            self.name,
            self.translate(_(self.time_format)),
            False, title=self.translate(_('Date selector')))
        return "%s\n%s" % (res, calendar_res)

    def _toFieldValue(self, input):
        if input == self._missing:
            return self.context.missing_value
        else:
            try:
                format = self.translate(_(self.time_format))
                return str2datetime(input, format).date()
            except (DateTimeError, ValueError, IndexError), v:
                raise ConversionError("Invalid datetime data", v)


class TimeWidget(TextWidget):

    displayWidth = 20

    def _getFormInput(self):
        return self.request.form[self.name + '_hour'] + ':' + \
               self.request.form[self.name + '_minute']

    def _toFieldValue(self, input):
        if input == self._missing:
            return self.context.missing_value
        else:
            try:
                hours, minutes = input.split(':')
                return time(hour=int(hours), minute=int(minutes))
            except (ValueError, IndexError), v:
                raise ConversionError("Invalid time", v)

    def _getDefault(self):
        # Get this from the field instead
        return time(hour=8,minute=0)

    def hasInput(self):
        for ext in ('_hour', '_minute'):
            if not self.name + ext in self.request.form:
                return False
        return True

    def __call__(self):
        value = self._getFormValue()
        hour_res = _makeHourDropDown(self.name + '_hour', selected=value.hour)
        minute_res = _makeMinuteDropDown(self.name + '_minute', selected=value.minute)
        return "\n".join([hour_res,minute_res])


# TODO: This should be refactored to support am/pm stuff.
def _makeHourDropDown(name, begins=0, ends=24, selected=None):
    """Creates a selects drop down for hours.

    The hour box begins at 'begins' and ends at one before 'ends'.
    If the selected hour is before of after the hours displayed, no
    hour will be selected.
    """
    elements = []
    for hour in range(begins, ends-begins):
        text = '%02d' % hour
        if selected == hour:
            element = renderElement('option',
                                    contents=text,
                                    value=text,
                                    selected='selected')
        else:
            element = renderElement('option',
                                    contents=text,
                                    value=text)
        elements.append(element)
    content = '\n'.join(elements)
    return renderElement('select',
                         name=name,
                         id=name,
                         contents=content)

def _makeMinuteDropDown(name, step=5, selected=None):
    """Creates a selects drop down for minutes.

    The minute box starts at 0 and will process with 'step' minutes at
    a time until it's over 60 minutes.
    If the minute selected is not one of the minutes displayed,
    the nearest *preceding* value will be selected.
    """
    elements = []
    for minute in range(0, 60, step):
        text = '%02d' % minute
        if selected >= minute and selected  < minute+step:
            element = renderElement('option',
                                    contents=text,
                                    value=text,
                                    selected='selected')
        else:
            element = renderElement('option',
                                    contents=text,
                                    value=text)
        elements.append(element)
    content = '\n'.join(elements)
    return renderElement('select',
                         name=name,
                         id=name,
                         contents=content)



# That uses a helper function--you'll see a Zope 2-ism you'll need to
# convert as well.  It's separate because I ended up wanting to use
# it for non-schema generated forms as well...

calendar_js_scripts = """\
<style type="text/css">@import url(++resource++calendar-win2k-1.css);</style>
<script type="text/javascript" src="++resource++calendar.js"></script>
<script type="text/javascript" src="++resource++calendar-%s.js"></script>
<script type="text/javascript" src="++resource++calendar-setup.js"></script>"""

calendar_js_template = """%s
<script type="text/javascript">
Calendar.setup({inputField: "%s", ifFormat: "%s", showsTime: %s,
                button: "%s", singleClick: true, firstDay: 1});
</script>"""

def make_calendar_widget(request,
    image_id, field_id, format, showsTime,
    image_zope_id='++resource++jscalendar.gif',
    style="cursor: pointer;",
    title="Date selector",
    onmouseover=r"this.style.background='black';",
    onmouseout=r"this.style.background=''"):

    image_tag = '<img src="%s" id="%s" style="%s" title="%s" '\
                'onmouseover="%s" onmouseout="%s"/>' % (
        image_zope_id, image_id, style, title, onmouseover, onmouseout)
         
    showsTime = showsTime and "true" or "false"
    result = calendar_js_template % (
        image_tag, field_id, format, showsTime, image_id)
    return make_calendar_js(request) + result

def make_calendar_js(request):
    if getattr(request, '_jscalendar_scripts_included', 0):
        return ''
    lang = getattr(request, 'jscalendar_language', 'en')
    request._jscalendar_scripts_included = 1
    return calendar_js_scripts % lang

def str2datetime(string, format=None):
    if format is None:
        return parseDatetimetz(string).replace(tzinfo=None)
    return datetime(*strptime(string, format)[:6])

# now for something completely different: a widget to display
# List fields with text contents as a textarea.

from zope.app.form.browser import TextAreaWidget
from sets import Set

class SetTextAreaWidget(TextAreaWidget):
    
    def __init__(self, field, vocabulary, request):
        """Initialize the widget."""
        # only allow this to happen for a bound field
        assert field.context is not None
        self.vocabulary = vocabulary
        super(SetTextAreaWidget, self).__init__(field, request)
        self.empty_marker_name = self.name + "-empty-marker"

    def _toFieldValue(self, value):
        value = super(SetTextAreaWidget, self)._toFieldValue(value)
        if value:
            value = value.split('\n')
        return Set(value)
    
    def _toFormValue(self, value):
        if value:
            value = '\n'.join(list(value))
        else:
            value = ''
        return super(SetTextAreaWidget, self)._toFormValue(value)


class EndBeforeStart(ValidationError):
    __doc__ = _("""End must come after start""")

class EndDateWidget(DivDatetimeWidget):
    """A special widget for end dates

    This widget will raise an error if it's value is lower than the
    value of the start time widget.
    """
    start_widget_id = 'dtstart'
    transparent_widget_id = 'transparent'
    
    def _toFieldValue(self, input):
        value = DivDatetimeWidget._toFieldValue(self, input)
        form = self.request.form
        try:
            name = 'field.'+self.start_widget_id
            startinput = form[name] + ' ' + \
                         form[name + '_hour'] + ':' + \
                         form[name + '_minute']
            startvalue = DivDatetimeWidget._toFieldValue(self, startinput)
        except InputErrors:
            return value
            
        # If it's an allday event, start date must be before or equal to
        # end date. Time is ignored.
        if (form.has_key('field.allday') and form['field.allday'] == u'on' and
            startvalue.date() <= value.date()):
            # Also, it should always end at 23:55, if it is an all day event.
            value = value.combine(value, time(23, 55))

        # Otherwise, start must be before end:
        if startvalue >= value:                
            # If neither of the above is true, then the end of the date comes
            # before the start of the date, and that's not allowed. Raise error:
            self._error = WidgetInputError(self.context.__name__, self.label,
                                           EndBeforeStart())
            raise self._error

        # Now check that all invited users that you are not manager for
        # are free during this time.
        if self.request.form.get('field.transparent') == u'on':
            # Transparent events should not be checked for conflicts.
            return value
        checker = IBusyChecker(self.context.context)
        try:
            checker.check(startvalue, value)
        except ValidationError, e:            
            self._error = WidgetInputError(self.context.__name__, self.label,
                                           e)
            raise self._error
        return value
    
    
