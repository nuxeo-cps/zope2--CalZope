��    �      �  �   �      �  !   �     �          %     @     I     O     d  (  t     �  	   �     �     �     �     �  	   �     �     	       	        "     0  !   4     V     _  
   m     x     �     �     �     �     �     �     �       	   %     /     ;     K     ]     n  
     
   �  
   �  
   �     �  �   �     �     �     �     �  	   �     �     �     �     �     �  �        �     �     �     �     �       )   #  *   M  =   x  �  �     X     r     �     �  	   �  &   �  �   �  "   �  %   �  0   !     R  7   k  	   �     �     �     �     �     �  
   �     �     �  
   �               $     3     B     P     ^     z     �     �     �     �     �     �     �     �               &     8     I     Z     k     |     �     �     �     �     �  "   �     �     �               0     D     X     n          �     �     �     �  !   �  
             "  
   1     <     H     `     }     �     �     �     �     �     �  !         8      S      h      ~      �      �      �      �      �   
   �   
   �   #   �      !     (!  '   G!      o!     �!     �!     �!     �!     �!  	   �!  	   �!  	   �!  	   �!  	   �!  	   �!  	   "     "     $"     6"     H"     Z"     l"     ~"     �"     �"     �"  �  �"  !   r$     �$     �$     �$     �$     �$     �$     %  &   %     E%  	   N%     X%     i%     y%     �%  	   �%     �%     �%     �%  	   �%     �%     �%  !   �%     &     &  
   ,&     7&     G&     Y&     f&     &     �&     �&     �&     �&  	   �&     �&     �&     '     '     0'  
   A'  
   L'  
   W'  
   b'     m'  9   �'     �'     �'     �'     �'  	   �'     (     (     (  
   #(     .(  %   <(     b(     j(     q(     (     �(     �(  )   �(  *   �(  =   )     D)     d)     ~)     �)     �)  	   �)  &   �)  ,   *  "   5*  %   X*  0   ~*     �*  7   �*  	    +     
+     +     +     "+     @+  
   F+     Q+     V+     Z+     ^+     e+     l+     s+     {+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+     �+  	   ,     ,     ,  _   ,     y,     �,  	   �,     �,     �,     �,     �,  
   �,     �,     �,  
   �,  	   �,  	   �,     �,     -     -     -     (-     --     0-     B-     Y-     b-     q-     �-  	   �-  
   �-     �-     �-     �-     �-     .     .     .     .     %.     +.     1.     :.     >.     C.     _.     a.     r.     �.     �.     �.     �.  0   �.     �.     �.     /  	   /     /     /     &/     //     6/     8/     :/     </     >/     @/     B/     D/     J/     P/     W   �   $   Q      0   �   �      8   P      e       �           l   D   n   �   �   �   6   i   �   L   �       |   J   �   .   �   �   m   U           �      y                   w       \   {   �       �      ~   �       #   X   u   z          �   +       5           �         *   7   �              �   ^           N   I       -   ]       f   �   �           �   4      j      1                 �   �   �   =   (   t   �   &   �   2   �   ?   %       `   �   �      T               9              �                  �   Z   �       �                     Y       �      K      <   S   H   �   k   o   p   q   r   d   @   "   g   h   V   a   _   ,              C   �           :   �       >             �       �              �   E   [   O   F       	       �       s   b   /   �       �   �   �   c   �   A           !   �   v          �   B       
           �         )   �   �   G   x   �       �          ;   }           �   �   �   3   �   M   '      �   R   �    ${amount} events that need action ${amount} events you attend ${amount} events you organize %(day)s %(month)s %(year)s %Y-%m-%d %d/%m , for ${count} times , until ${date} A set of weekdays when this event occurs.

        Weekdays are represented as integers from 0 (Monday) to 6 (Sunday).
        This is what the `calendar` and `datetime` modules use.

        The event repeats on the weekday of the first occurence even
        if that weekday is not in this set. ACCEPTED Add event AttendeeManager AttendeeReader CANCELED CONFIDENTIAL CONFIRMED Categories for this event Count DECLINED DELEGATED Date selector Day Do you want to delete this event? Duration Edit calendar Edit event EventOrganizer EventParticipant EventReader Events you are attending Events you organize Every ${count} days Every ${count} months Every ${count} weeks Every ${count} years Every day Every month Every other day Every other month Every other week Every other year Every week Every year First date INDIVIDUAL Import iCalendar file Interval of recurrence (a positive integer).

        For example, to indicate that an event occurs every second day,
        you would create a DailyRecurrenceRule witl interval equal to 2. Invalid duration Invalid integer data Invalid time Invalid value Last date Month More... NEEDS-ACTION No events to list No recurrence Number of times the event is repeated.

        Can be None or an integer value.  If count is not None then
        until must be None.  If both count and until are None the
        event repeats forever. PRIVATE PUBLIC Private Event RESOURCE Required input is missing. Search between Search in full names and titles of users. Selects the recurrence rule for the object Some attendees are busy during the selected period: %(users)s Specification of monthly occurence behaviour.

        Can be one of three values: 'monthday', 'weekday', 'lastweekday'.

        'monthday'    specifies that the event recurs on the same day of month
                      (e.g., 25th day of a month).

        'weekday'     specifies that the event recurs on the same week
                      within a month on the same weekday, indexed from the
                      first (e.g. 3rd Friday of a month).

        'lastweekday' specifies that the event recurs on the same week
                      within a month on the same weekday, indexed from the
                      end of month (e.g. 2nd last Friday of a month). Start search at this hour Start searching from this date. Stop search at this hour Stop searching after this date. TENTATIVE The attendee is busy during this event The date of the last recurrence of the event.

        Can be None or a datetime.date instance.  If until is not None
        then count must be None.  If both count and until are None the
        event repeats forever. The expected duration of the event There are ${num_errors} input errors. This attendee is busy during the selected period Updated on %(date_time)s Use * to list all attendees (may take a very long time) WORKSPACE Week Week ${week} Weeks Who has access to this event. Width YYYY-MM-DD Year and button_add button_cancel button_change button_confirm button_refresh button_remove button_search button_search_for_free_time button_submit calendar_day_0 calendar_day_1 calendar_day_2 calendar_day_3 calendar_day_4 calendar_day_5 calendar_day_6 calendar_month_1 calendar_month_10 calendar_month_11 calendar_month_12 calendar_month_2 calendar_month_3 calendar_month_4 calendar_month_5 calendar_month_6 calendar_month_7 calendar_month_8 calendar_month_9 day days description_multiple_calendar_view filename_label label_access label_add_event label_attached_document label_attendee_list label_attendee_name label_attendee_status label_categories label_current_attendees label_current_day label_current_month label_current_week label_current_year label_currently_visible_calendars label_date label_description label_duration label_ends label_false label_list_of_attendees label_list_of_matching_times label_location label_meeting_helper label_multiple_calendar_view label_no_attendees_selected label_organizer label_recurrence label_search_for_attendees label_search_for_calendars_to_add label_search_for_free_time label_search_results label_select_timespan label_start label_starts label_status label_title label_today label_transparent label_true label_type message_events_action_is_needed_for message_see_this_events_postfix message_see_this_events_prefix message_select_new_participation_status message_this_is_an_all_day_event month months psm_file_uploaded transparent_description week weekday_0 weekday_1 weekday_2 weekday_3 weekday_4 weekday_5 weekday_6 weekday_initial_0 weekday_initial_1 weekday_initial_2 weekday_initial_3 weekday_initial_4 weekday_initial_5 weekday_initial_6 weeks years you have Project-Id-Version: en
POT-Creation-Date: 2005-10-02 14:40default
PO-Revision-Date: 2005-09-09 16:59+0200
Last-Translator: Lennart Regebro <regebro@nuxeo.com>
Language-Team: English <cps-devel@lists.nuxeo.com>
MIME-Version: 1.0
Content-Type: text/plain; charset=ISO-8859-15
Content-Transfer-Encoding: 8bit
Plural-Forms:  nplurals=2; plural=(n != 1);
Language-Code: en
Language-Name: English
Preferred-Encodings: latin9
Domain: default
X-Generator: KBabel 1.10
 ${amount} events that need action ${amount} events you attend ${amount} events you organize %(month)s %(day)s, %(year)s %m/%d/%Y %m/%d , for ${count} times , until ${date} Select which weekdays the event occurs Accepted Add event Calendar Manager Calendar Reader Canceled Confidential Confirmed Categories for this event Total number of occurences Declined Delegated Date selector Day Do you want to delete this event? Duration Edit calendar Edit event Event Organizer Event Participant Event Reader Events you are attending Events you organize Every ${count} days Every ${count} months Every ${count} weeks Every ${count} years Every day Every month Every other day Every other month Every other week Every other year Every week Every year First date Individual Import iCalendar file 1 means every time, 2 every second time, 3 every third... Invalid duration Invalid integer data Invalid time Invalid value Last date Month More... Needs Action No events. No recurrence Number of times the event is repeated Private Public Private Event Resource Required input is missing Search between Search in full names and titles of users. Selects the recurrence rule for the object Some attendees are busy during the selected period: %(users)s Behaviour of monthly recurrence Start search at this hour Start searching from this date. Stop search at this hour Stop searching after this date. Tentative The attendee is busy during this event The date of the last recurrence of the event The expected duration of the event There are ${num_errors} input errors. This attendee is busy during the selected period Updated on %(date_time)s Use * to list all attendees (may take a very long time) Workspace Week Week ${week} Weeks Who has access to this event. Width MM/DD/YYYY Year and Add Cancel Change Delete Refresh Remove Search Search for free time Submit Mo Tu We Th Fr Sa Su January October November December February March April May June July August September day days With multiple calendar view, you can see the events from several calendars as if they were one. Filename Access Add event Document List of attendees Name Status Categories Current attendees Today This Month This Week This Year Current attendees Date Description Duration Ends No List of attendees List of matching times Location Meeting helper Multiple calendar view No attendees selected Organizer Recurrence Search for attendees Search for attendees Search for free time Search results Select Timespan Start Starts Status Title Today Not Busy Yes Type Events action is needed for . see this event's Select new participation status This is an all-day event. month months File uploaded You can be invited to meetings during this event week Monday Tuesday Wednesday Thursday Friday Saturday Sunday M T W T F S S weeks years you have 