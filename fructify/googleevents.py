"""Functions for events from Google Calendar."""

from datetime import datetime, timezone

from zoneinfo import ZoneInfo


def parse_event_time(time_playload, calendar_tz):
    """
    Parse a Gcal event time and timezone and return a naive datetime in UTC.

    The payload has different fields for a full datetime or just a date. Datetimes are
    assumed to be in UTC already as that can be forced in the Gcal request. Dates are
    for all day events, so the day begins at 0000 in the calendar's timezone.
    """
    if "date" in time_playload:
        midnight = datetime.strptime(time_playload["date"], "%Y-%m-%d")
        aware_time = midnight.replace(tzinfo=ZoneInfo(calendar_tz))
        return aware_time.astimezone(timezone.utc).replace(tzinfo=None)
    return datetime.strptime(time_playload["dateTime"], "%Y-%m-%dT%H:%M:%SZ")


def find_next_event_start(events_obj, now):
    """
    Find the start time of the next event after now from a google calendar response.

    You can only query for events ending after a certain time, so some events in the
    response could start before that time. The response should be sorted by start time
    already.
    """
    calendar_tz = events_obj["timeZone"]
    for event in events_obj["items"]:
        event_start = parse_event_time(event["start"], calendar_tz)
        if event_start > now:
            return event_start
    else:  # no break
        raise LookupError("All events are before now")


def find_event_summaries_starting(events_obj, start):
    """
    Find events starting at start in google calendar response and return summaries.

    Events should already be sorted.
    """
    calendar_tz = events_obj["timeZone"]
    for event in events_obj["items"]:
        event_start = parse_event_time(event["start"], calendar_tz)
        if event_start > start:
            break
        if event_start == start:
            yield event["summary"]
