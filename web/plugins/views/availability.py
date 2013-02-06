#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2013             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

import table
from valuespec import *

# Function building the availability view
def render_availability(view, datasource, filterheaders, display_options, 
                        only_sites, limit):
    timeline = not not html.var("timeline")
    if timeline:
        tl_site = html.var("timeline_site")
        tl_host = html.var("timeline_host")
        tl_service = html.var("timeline_service")
        title = _("Timeline of") + " " + tl_host
        if tl_service:
            title += ", " + tl_service
        timeline = (tl_site, tl_host, tl_service)

    else:
        title = _("Availability: ") + view_title(view)
    if 'H' in display_options:
        html.body_start(title, stylesheets=["pages","views","status"])
    if 'T' in display_options:
        html.top_heading(title)
    if 'B' in display_options:
        html.begin_context_buttons()
        togglebutton("avoptions", False, "painteroptions", _("Configure details of the report"))
        html.context_button(_("Status View"), html.makeuri([("mode", "status")]), "status")
        if timeline:
            html.context_button(_("Availability"), html.makeuri([("timeline", "")]), "availability")
        html.end_context_buttons()

    avoptions = render_availability_options()
    if not html.has_user_errors():
        range, range_title = avoptions["range"]
        rows = get_availability_data(datasource, filterheaders, range, only_sites, limit, timeline)
        has_service = "service" in datasource["infos"]
        do_render_availability(rows, has_service, avoptions, timeline)

    if 'Z' in display_options:
        html.bottom_footer()
    if 'H' in display_options:
        html.body_end()

avoption_entries = [
  # Time range selection
  ( "rangespec",
    "double",
    CascadingDropdown(
        title = _("Time range"),
        choices = [

            ( "d0",  _("Today") ),
            ( "d1",  _("Yesterday") ),

            ( "w0",  _("This week") ),
            ( "w1",  _("Last week") ),

            ( "m0",  _("This month") ),
            ( "m1",  _("Last month") ),

            ( "y0",  _("This year") ),
            ( "y1",  _("Last year") ),

            ( "age", _("The last..."), Age() ),
            ( "date", _("Explicit date..."), 
                Tuple(
                    orientation = "horizontal",
                    title_br = False,
                    elements = [
                        AbsoluteDate(title = _("From:")),
                        AbsoluteDate(title = _("To:")),
                    ],
                ),
            ),
        ],
        default_value = "m1",
    )
  ),

  # How to deal with downtimes, etc.
  ( "consider", 
    "double",
    Dictionary( 
       title = _("Status Classification"),
       columns = 2,
       elements = [
           ( "flapping", 
              Checkbox(label = _("Consider periods of flapping states")),
           ),
           ( "downtime", 
              Checkbox(label = _("Consider scheduled downtimes")),
           ),
           ( "host_down", 
              Checkbox(label = _("Consider times where the host is down")),
           ),
           ( "notification_period", 
              Checkbox(label = _("Consider notification period")),
           ),
           ( "unmonitored",
              Checkbox(label = _("Include unmonitored time")),
           ),
       ],
       optional_keys = False,
    ),
  ),

  # Optionally group some states togehter
  ( "state_grouping", 
    "double",
    Dictionary( 
       title = _("Status Grouping"),
       columns = 2,
       elements = [
           ( "warn", 
              DropdownChoice(
                  label = _("Treat Warning as: "),
                  choices = [ 
                    ( "ok",      _("OK") ),
                    ( "warn",    _("WARN") ),
                    ( "crit",    _("CRIT") ),
                    ( "unknown", _("UNKNOWN") ),
                  ]
                ),
           ),
           ( "unknown", 
              DropdownChoice(
                  label = _("Treat Unknown as: "),
                  choices = [ 
                    ( "ok",      _("OK") ),
                    ( "warn",    _("WARN") ),
                    ( "crit",    _("CRIT") ),
                    ( "unknown", _("UNKNOWN") ),
                  ]
                ),
           ),
           ( "host_down", 
              DropdownChoice(
                  label = _("Treat Host Down as: "),
                  choices = [ 
                    ( "ok",        _("OK") ),
                    ( "warn",      _("WARN") ),
                    ( "crit",      _("CRIT") ),
                    ( "unknown",   _("UNKNOWN") ),
                    ( "host_down", _("Host Down") ),
                  ]
                ),
           ),
       ],
       optional_keys = False,
    ),
  ),
  # Format of numbers
  ( "timeformat",
    "single",
    DropdownChoice(
        title = _("Format time ranges as"),
        choices = [
            ("percentage_0", _("Percentage - XX %") ),
            ("percentage_1", _("Percentage - XX.X %") ),
            ("percentage_2", _("Percentage - XX.XX %") ),
            ("percentage_3", _("Percentage - XX.XXX %") ),
            ("seconds",      _("Seconds") ),
            ("minutes",      _("Minutes") ),
            ("hours",        _("Hours") ),
            ("hhmmss",       _("HH:MM:SS") ),
        ],
    )
  ),


  # Short time intervals
  ( "short_intervals",
    "single",
    Integer(
        title = _("Short Time Intervalls"),
        minvalue = 0,
        unit = _("sec"),
        label = _("Ignore intervals shorter or equal"),
    ),
  ),
]


def render_availability_options():
    avoptions = config.load_user_file("avoptions", {
        "range"          : (time.time() - 86400, time.time()),
        "consider"       : {
            "flapping"            : True,
            "downtime"            : True,
            "host_down"           : True,
            "notification_period" : True,
            "unmonitored"         : True,
        },
        "timeformat"     : "percentage_2",
        "rangespec"      : "d0",
        "state_grouping" : {
            "warn"      : "warn",
            "unknown"   : "unknown",
            "host_down" : "host_down",
        },
        "short_intervals" : 0,
    })

    is_open = False
    html.begin_form("avoptions")
    html.hidden_field("avoptions", "set")
    html.write('<div class="view_form" id="avoptions" %s>' 
            % (not is_open and 'style="display: none"' or '') )
    html.write("<table border=0 cellspacing=0 cellpadding=0 class=filterform><tr><td>")

    if html.var("avoptions") == "set":
        for name, height, vs in avoption_entries:
            try:
                avoptions[name] = vs.from_html_vars("avo_" + name)
            except MKUserError, e:
                html.add_user_error(e.varname, e.message)
    
    try:
        range, range_title = compute_range(avoptions["rangespec"])
        avoptions["range"] = range, range_title
    except MKUserError, e:
        html.add_user_error(e.varname, e.message)

    if html.has_user_errors():
        html.show_user_errors()

    for name, height, vs in avoption_entries:
        html.write('<div class="floatfilter %s %s">' % (height, name))
        html.write('<div class=legend>%s</div>' % vs.title())
        html.write('<div class=content>')
        vs.render_input("avo_" + name, avoptions.get(name))
        html.write("</div>")
        html.write("</div>")
    
    html.write("</td></tr>")

    html.write("<tr><td>")
    html.button("apply", _("Apply"), "submit")
    html.write("</td></tr></table>")
    html.write("</div>")

    html.hidden_fields()
    html.end_form()

    if html.form_submitted():
        config.save_user_file("avoptions", avoptions)

    return avoptions

month_names = [
  _("January"), _("February"), _("March"), _("April"),
  _("May"), _("June"), _("July"), _("August"),
  _("September"), _("October"), _("November"), _("December")
]

def compute_range(rangespec):
    now = time.time()
    if rangespec[0] == 'age':
        from_time = now - rangespec[1]
        until_time = now
        title = _("The last ") + Age().value_to_text(rangespec[1])
        return (from_time, until_time), title
    elif rangespec[0] == 'date':
        from_time, until_time = rangespec[1]
        if from_time > until_time:
            raise MKUserError("avo_rangespec_9_0_year", _("The end date must be after the start date"))
        until_time += 86400 # Consider *end* of this day
        title = AbsoluteDate().value_to_text(from_time) + " ... " + \
                AbsoluteDate().value_to_text(until_time)
        return (from_time, until_time), title

    else:
        # year, month, day_of_month, hour, minute, second, day_of_week, day_of_year, is_daylightsavingtime
        broken = list(time.localtime(now))
        broken[3:6] = 0, 0, 0 # set time to 00:00:00
        midnight = time.mktime(broken)

        until_time = now
        if rangespec[0] == 'd': # this/last Day
            from_time = time.mktime(broken)
            titles = _("Today"), _("Yesterday")

        elif rangespec[0] == 'w': # week
            from_time = midnight - (broken[6]) * 86400
            titles = _("This week"), _("Last week")

        elif rangespec[0] == 'm': # month
            broken[2] = 1
            from_time = time.mktime(broken)
            titles = month_names[broken[1] - 1] + " " + str(broken[0]), \
                     month_names[(broken[1] + 10) % 12] + " " + str(broken[0])

        elif rangespec[0] == 'y': # year
            broken[1:3] = [1, 1]
            from_time = time.mktime(broken)
            titles = str(broken[0]), str(broken[0]-1)

        if rangespec[1] == '0':
            return (from_time, now), titles[0]

        else: # last (previous)
            if rangespec[0] == 'd':
                return (from_time - 86400, from_time), titles[1]
            elif rangespec[0] == 'w':
                return (from_time - 7 * 86400, from_time), titles[1]

            until_time = from_time
            from_broken = list(time.localtime(from_time))
            if rangespec[0] == 'y':
                from_broken[0] -= 1
            else: # m
                from_broken[1] -= 1
                if from_broken[1] == 0:
                    from_broken[1] = 12
                    from_broken[0] -= 1
            return (time.mktime(from_broken), until_time), titles[1]

def get_availability_data(datasource, filterheaders, range, only_sites, limit, timeline):
    has_service = "service" in datasource["infos"]
    av_filter = "Filter: time >= %d\nFilter: time <= %d\n" % range
    if timeline:
        tl_site, tl_host, tl_service = timeline
        av_filter += "Filter: host_name = %s\nFilter: service_description = %s\n" % (
                tl_host, tl_service)
        only_sites = [ tl_site ]
    elif has_service:
        av_filter += "Filter: service_description !=\n"
    else:
        av_filter += "Filter: service_description =\n"


    query = "GET statehist\n" + av_filter

    # Add Columns needed for object identification
    columns = [ "host_name", "service_description" ]

    # Columns for availability
    columns += [
      "duration", "from", "until", "state", "host_down", "in_downtime", 
      "in_host_downtime", "in_notification_period", "is_flapping", 
      "log_output" ]
    if timeline:
        columns.append("log_output")

    add_columns = datasource.get("add_columns", [])
    rows = do_query_data(query, columns, add_columns, None, filterheaders, only_sites, limit)
    return rows
            

host_availability_columns = [
 ( "up",                        "state0",        _("UP"),       None ),
 ( "down",                      "state2",        _("DOWN"),     None ),
 ( "unreach",                   "state3",        _("UNREACH"),  None ),
 ( "flapping",                  "flapping",      _("Flapping"), None ),
 ( "in_downtime",               "downtime",      _("Downtime"), _("The host was in a scheduled downtime") ),
 ( "outof_notification_period", "",              _("OO/Notif"), _("Out of Notification Period") ),
 ( "unmonitored",               "unmonitored",   _("N/A"),      _("During this time period no monitoring data is available") ),
]

service_availability_columns = [
 ( "ok",                        "state0",        _("OK"),       None ),
 ( "warn",                      "state1",        _("WARN"),     None ),
 ( "crit",                      "state2",        _("CRIT"),     None ),
 ( "unknown",                   "state3",        _("UNKNOWN"),  None ),
 ( "flapping",                  "flapping",      _("Flapping"), None ),
 ( "host_down",                 "hostdown",      _("H.Down"),   _("The host was down") ),
 ( "in_downtime",               "downtime",      _("Downtime"), _("The host or service was in a scheduled downtime") ),
 ( "outof_notification_period", "",              _("OO/Notif"), _("Out of Notification Period") ),
 ( "unmonitored",               "unmonitored",   _("N/A"),      _("During this time period no monitoring data is available") ),
]

bi_availability_columns = [
 ( "ok",                        "state0",        _("OK"),       None ),
 ( "warn",                      "state1",        _("WARN"),     None ),
 ( "crit",                      "state2",        _("CRIT"),     None ),
 ( "unknown",                   "state3",        _("UNKNOWN"),  None ),
 ( "unmonitored",               "unmonitored",   _("N/A"),      _("During this time period no monitoring data is available") ),
]

def do_render_availability(rows, has_service, avoptions, timeline):
    # Sort by site/host and service, while keeping native order
    by_host = {}
    for row in rows:
        site_host = row["site"], row["host_name"]
        service = row["service_description"]
        by_host.setdefault(site_host, {})
        by_host[site_host].setdefault(service, []).append(row)

    # Now compute availability table. We have the following possible states:
    # 1. "unmonitored"
    # 2. "monitored"
    #    2.1 "outof_notification_period"
    #    2.2 "in_notification_period"
    #         2.2.1 "in_downtime" (also in_host_downtime)
    #         2.2.2 "not_in_downtime"
    #               2.2.2.1 "host_down"
    #               2.2.2.2 "host not down"
    #                    2.2.2.2.1 "ok"
    #                    2.2.2.2.2 "warn"
    #                    2.2.2.2.3 "crit"
    #                    2.2.2.2.4 "unknown"
    availability = []
    # Note: in case of timeline, we have data from exacly one host/service
    for site_host, site_host_entry in by_host.iteritems():
        for service, service_entry in site_host_entry.iteritems():

            # First compute timeline
            timeline_rows = []
            considered_duration = 0
            for span in service_entry:
                state = span["state"]
                if state == -1:
                    s = "unmonitored"
                    if not avoptions["consider"]["unmonitored"]:
                        continue
                elif span["in_notification_period"] == 0 and avoptions["consider"]["notification_period"]:
                    s = "outof_notification_period"
                elif (span["in_downtime"] or span["in_host_downtime"]) and avoptions["consider"]["downtime"]:
                    s = "in_downtime"
                elif span["host_down"] and avoptions["consider"]["host_down"]:
                    s = "host_down"
                elif span["is_flapping"] and avoptions["consider"]["flapping"]:
                    s = "flapping"
                else:
                    if has_service:
                        s = { 0: "ok", 1:"warn", 2:"crit", 3:"unknown" }[state]
                    else:
                        s = { 0: "up", 1:"down", 2:"unreach"}[state]
                    if s == "warn":
                        s = avoptions["state_grouping"]["warn"]
                    elif s == "unknown": 
                        s = avoptions["state_grouping"]["unknown"]
                    elif s == "host_down":
                        s = avoptions["state_grouping"]["host_down"]

                considered_duration += span["duration"]
                timeline_rows.append((span, s))

            # Now merge consecutive rows with identical state
            merge_timeline(timeline_rows)

            # Melt down short intervals
            if avoptions["short_intervals"]:
                melt_short_intervals(timeline_rows, avoptions["short_intervals"])

            # Condense into availability
            states = {}
            for span, s in timeline_rows:
                states.setdefault(s, 0)
                states[s] += span["duration"]

            availability.append([site_host[0], site_host[1], service, states, considered_duration])


    # Prepare number format function
    range, range_title = avoptions["range"]
    from_time, until_time = range
    duration = until_time - from_time
    timeformat = avoptions["timeformat"]
    if timeformat.startswith("percentage_"):
        def render_number(n, d):
            if not d:
                return _("n/a")
            else:
                return ("%." + timeformat[11:] + "f%%") % ( float(n) / float(d) * 100.0)
    elif timeformat == "seconds":
        def render_number(n, d):
            return "%d s" % n
    elif timeformat == "minutes":
        def render_number(n, d):
            return "%d min" % (n / 60)
    elif timeformat == "hours":
        def render_number(n, d):
            return "%d h" % (n / 3600)
    else:
        def render_number(n, d):
            minn, sec = divmod(n, 60)
            hours, minn = divmod(minn, 60)
            return "%02d:%02d:%02d" % (hours, minn, sec)

    if timeline:
        render_timeline(timeline_rows, from_time, until_time, considered_duration, timeline, range_title, render_number)
    else:
        render_availability_table(availability, from_time, until_time, range_title, has_service, avoptions, render_number)

def render_timeline(timeline_rows, from_time, until_time, considered_duration, timeline, range_title, render_number):
    if not timeline_rows:
        html.write('<div class=info>%s</div>' % _("No information available"))
        return

    # Timeformat: show date only if the displayed time range spans over
    # more than one day.
    format = "%H:%M:%S"
    if time.localtime(from_time)[:3] != time.localtime(until_time-1)[:3]:
        format = "%Y-%m-%d " + format
    def render_date(ts):
        return time.strftime(format, time.localtime(ts))

    if type(timeline) == tuple:
        tl_site, tl_host, tl_service = timeline
        title = _("Timeline of") + " " + tl_host
        if tl_service:
            title += ", " + tl_service
            availability_columns = service_availability_columns
        else:
            availability_columns = host_availability_columns
    else:
        title = "BI Aggregate " + timeline
        availability_columns = bi_availability_columns

    title += " - " + range_title

    # Render graphical representation
    # Make sure that each cell is visible, if possible
    min_percentage = min(100.0 / len(timeline_rows), 1)
    rest_percentage = 100 - len(timeline_rows) * min_percentage
    html.write('<div class=timelinerange>')
    html.write('<div class=from>%s</div><div class=until>%s</div></div>' % (
        render_date(from_time), render_date(until_time)))
    
    html.write('<table class=timeline>')
    html.write('<tr class=timeline>')
    for row_nr, (row, state_id) in enumerate(timeline_rows):
        for sid, css, sname, help in availability_columns:
            if sid == state_id:
                title = _("From %s until %s (%s) %s") % (
                    render_date(row["from"]), render_date(row["until"]),
                    render_number(row["duration"], considered_duration),
                    sname)
                if row["log_output"]:
                    title += " - " + row["log_output"]
                width = min_percentage + rest_percentage * row["duration"] / considered_duration
                html.write('<td onmouseover="timeline_hover(%d, 1);" onmouseout="timeline_hover(%d, 0);" '
                           'style="width: %.1f%%" title="%s" class="%s"></td>' % (
                           row_nr, row_nr, width, title, css))
    html.write('</tr></table>')

    # Render Table
    table.begin("", css="timelineevents")
    for row_nr, (row, state_id) in enumerate(timeline_rows):
        table.row()
        table.cell(_("From"), render_date(row["from"]), css="nobr narrow")
        table.cell(_("Until"), render_date(row["until"]), css="nobr narrow")
        table.cell(_("Duration"), render_number(row["duration"], considered_duration), css="number")
        for sid, css, sname, help in availability_columns:
            if sid == state_id:
                table.cell(_("State"), sname, css=css + " state narrow")
        table.cell(_("Plugin output"), row["log_output"])

    table.end()


# Merge consecutive rows with same state
def merge_timeline(entries):
    n = 1
    while n < len(entries):
        if entries[n][1] == entries[n-1][1]:
            entries[n-1][0]["duration"] += entries[n][0]["duration"]
            entries[n-1][0]["until"] = entries[n][0]["until"]
            del entries[n]
        else:
            n += 1

def melt_short_intervals(entries, duration):
    n = 1
    need_merge = False
    while n < len(entries) - 1:
        if entries[n][0]["duration"] <= duration and \
            entries[n-1][1] == entries[n+1][1]:
            entries[n] = (entries[n][0], entries[n-1][1])
            need_merge = True
        n += 1

    # Due to melting, we need to merge again
    if need_merge:
        merge_timeline(entries)
        melt_short_intervals(entries, duration)

def render_availability_table(availability, from_time, until_time, range_title, has_service, avoptions, render_number):
    # Some columns might be unneeded due to state treatment options
    sg = avoptions["state_grouping"]
    sgs = [ sg["warn"], sg["unknown"], sg["host_down"] ]

    # Render the stuff
    availability.sort()
    table.begin(_("Availability") + " " + range_title, css="availability")
    for site, host, service, states, considered_duration in availability:
        table.row()
        table.cell("", css="buttons")
        history_url_vars = [
            ("site", site),
            ("host", host),
            ("logtime_from_range", "unix"),  # absolute timestamp
            ("logtime_until_range", "unix"), # absolute timestamp
            ("logtime_from", str(int(from_time))),
            ("logtime_until", str(int(until_time)))]
        if has_service:
            history_url_vars += [
                ("service", service),
                ("view_name", "svcevents"),
            ]
        else:
            history_url_vars += [
                ("view_name", "hostevents"),
            ]

        timeline_url = html.makeuri([
               ("timeline", "yes"), 
               ("timeline_site", site), 
               ("timeline_host", host), 
               ("timeline_service", service)])
        html.icon_button(timeline_url, _("Timeline"), "timeline")
        history_url = "view.py?" + htmllib.urlencode_vars(history_url_vars)
        html.icon_button(history_url, _("Event History"), "history")
        host_url = "view.py?" + htmllib.urlencode_vars([("view_name", "hoststatus"), ("site", site), ("host", host)])
        table.cell(_("Host"), '<a href="%s">%s</a>' % (host_url, host))
        service_url = "view.py?" + htmllib.urlencode_vars([("view_name", "service"), ("site", site), ("host", host), ("service", service)])
        table.cell(_("Service"), '<a href="%s">%s</a>' % (service_url, service))
        if has_service:
            availability_columns = service_availability_columns
        else:
            availability_columns = host_availability_columns
        for sid, css, sname, help in availability_columns:
            if sid == "outof_notification_period" and not avoptions["consider"]["notification_period"]:
                continue
            elif sid == "in_downtime" and not avoptions["consider"]["downtime"]:
                continue
            elif sid == "unmonitored" and not avoptions["consider"]["unmonitored"]:
                continue
            elif sid in [ "warn", "unknown", "host_down" ] and sid not in sgs:
                continue
            number = states.get(sid, 0)
            if not number:
                css = ""
            table.cell(sname, render_number(number, considered_duration), css="number " + css, help=help)
    table.end()



# Render availability of an BI aggregate. This is currently
# no view and does not support display options
def render_bi_availability(tree):
    reqhosts = tree["reqhosts"]
    timeline = html.var("timeline")
    title = _("Availability of ") + tree["title"]
    html.body_start(title, stylesheets=["pages","views","status"])
    html.top_heading(title)
    html.begin_context_buttons()
    togglebutton("avoptions", False, "painteroptions", _("Configure details of the report"))
    html.context_button(_("Status View"), "view.py?" + 
            htmllib.urlencode_vars([("view_name", "aggr_single"),
              ("aggr_name", tree["title"])]), "showbi")
    if timeline:
        html.context_button(_("Availability"), html.makeuri([("timeline", "")]), "availability")
    else:
        html.context_button(_("Timeline"), html.makeuri([("timeline", "1")]), "timeline")
    html.end_context_buttons()

    avoptions = render_availability_options()
    if not html.has_user_errors():
        rows = get_bi_timeline(tree, avoptions)
        do_render_availability(rows, True, avoptions, timeline)

    html.bottom_footer()
    html.body_end()

def get_bi_timeline(tree, avoptions):
    range, range_title = avoptions["range"]
    # Get state history of all hosts and services contained in the tree.
    # In order to simplify the query, we always fetch the information for
    # all hosts of the aggregates.
    only_sites = set([])
    hosts = []
    for site, host in tree["reqhosts"]:
        only_sites.add(site)
        hosts.append(host)

    columns = [ "host_name", "service_description", "from", "log_output", "state" ]
    html.live.set_only_sites(list(only_sites))
    html.live.set_prepend_site(True)
    html.live.set_limit() # removes limit
    query = "GET statehist\n" + \
            "Columns: " + " ".join(columns) + "\n" +\
            "Filter: time >= %d\nFilter: time <= %d\n" % range

    for host in hosts:
        query += "Filter: host_name = %s\n" % host
    query += "Or: %d\n" % len(hosts)
    data = html.live.query(query)
    html.live.set_prepend_site(False)
    html.live.set_only_sites(None)
    columns = ["site"] + columns
    rows = [ dict(zip(columns, row)) for row in data ]

    # Now comes the tricky part: recompute the state of the aggregate
    # for each step in the state history and construct a timeline from
    # it. As a first step we need the start state for each of the
    # hosts/services. They will always be the first consecute rows
    # in the statehist table

    # First partition the rows into sequences with equal start time
    phases = {}
    for row in rows:
        from_time = row["from"]
        phases.setdefault(from_time, []).append(row)

    # Convert phases to sorted list
    sorted_times = phases.keys()
    sorted_times.sort()
    phases_list = []
    for from_time in sorted_times:
        phases_list.append((from_time, phases[from_time]))

    states = {}
    def update_states(phase_entries):
        for row in phase_entries:
            service = row["service_description"]
            key = row["site"], row["host_name"], service
            states[key] = row["state"], row["log_output"]


    update_states(phases_list[0][1])
    # states does now reflect the host/services states at the beginning
    # of the query range.
    tree_state = compute_tree_state(tree, states)
    tree_time = range[0]

    timeline = []
    def append_to_timeline(from_time, until_time, tree_state):
        timeline.append({"state" : tree_state[0]['state'],
                         "log_output" : tree_state[0]['output'],
                         "from" : from_time,
                         "until" : until_time,
                         "site" : "",
                         "host_name" : "",
                         "service_description" : tree['title'],
                         "in_notification_period" : 1,
                         "in_downtime" : 0,
                         "in_host_downtime" : 0,
                         "host_down" : 0,
                         "is_flapping" : 0,
                         "duration" : until_time - from_time,
        })


    for from_time, phase in phases_list[1:]:
        update_states(phase)
        next_tree_state = compute_tree_state(tree, states)
        duration = from_time - tree_time
        append_to_timeline(tree_time, from_time, tree_state)
        tree_state = next_tree_state
        tree_time = from_time

    # Add one last entry - for the state until the end of the interval
    append_to_timeline(tree_time, range[1], tree_state)

    # html.debug(timeline)
    return timeline

def compute_tree_state(tree, status):
    # Convert our status format into that needed by BI
    services_by_host = {}
    hosts = {}
    for site_host_service, state_output in status.items():
        site_host = site_host_service[:2]
        service = site_host_service[2]
        if service:
            services_by_host.setdefault(site_host, []).append((
                service, state_output[0], 1, state_output[1]))
        else:
            hosts[site_host] = state_output

    status_info = {}
    for site_host, state_output in hosts.items():
        status_info[site_host] = [
            state_output[0],
            state_output[1],
            services_by_host[site_host]
        ]


    # Finally we can execute the tree
    bi.g_assumptions = {}
    tree_state = bi.execute_tree(tree, status_info)
    return tree_state


# Av Options:
# Zeitspannen < X Minuten nicht werten
# Verhalten bei Flapping

# Idee:
# Bei OK während Downtime OK Vorrang lassen (einstellbar)
