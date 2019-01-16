import json
import traceback
import urllib2
import urlparse
from contextlib import closing
from datetime import datetime


def wedding(environ, start_response):
    days = days_until(datetime.today(), datetime(2020, 10, 10))
    request = urllib2.Request(
        "https://maker.ifttt.com/trigger/notify/with/key/dnaJW0wSYg5wScT5JZi-_o",
        '{{"value1": "{} days until wedding."}}'.format(days),
        {"Content-type": "application/json"},
    )
    with closing(urllib2.urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def debug(environ, start_response):
    start_response("200 OK", [("Content-type", "application/json")])
    return [json.dumps(urlparse.parse_qs(environ["QUERY_STRING"]), indent=2)]


def dropbox_debug(environ, start_response):
    request = urllib2.Request(
        "https://maker.ifttt.com/trigger/dropbox-debug/with/key/dnaJW0wSYg5wScT5JZi-_o",
        json.dumps(
            {"value1": json.dumps(urlparse.parse_qs(environ["QUERY_STRING"]), indent=2)}
        ),
        {"Content-type": "application/json"},
    )
    with closing(urllib2.urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


def days_until_route(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        start_response("405 Method not allowed", [("Content-type", "text/plain")])
        return ["POST only please"]
    with closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read()
    parsed_request = json.loads(request_body)
    from_date = parsed_request["from_date"]
    target_date = parsed_request["target_date"]
    target_label = parsed_request["target_label"]
    parsed_from_date = datetime.strptime(from_date, "%B %d, %Y at %I:%M%p")
    parsed_target_date = datetime.strptime(target_date, "%Y-%m-%d")
    safe_target_label = target_label[:50]
    days = days_until(parsed_from_date, parsed_target_date)
    request = urllib2.Request(
        "https://maker.ifttt.com/trigger/notify/with/key/dnaJW0wSYg5wScT5JZi-_o",
        json.dumps(
            {
                "value1": "{days} days until {target_label}.".format(
                    days=days, target_label=target_label
                ),
            }
        ),
        {"Content-type": "application/json"},
    )
    with closing(urllib2.urlopen(request)) as response:
        lines = list(response.readlines())
    start_response("200 OK", [("Content-type", "text/plain")])
    return lines


routes = {
    "/v1/wedding": wedding,
    "/v1/debug": debug,
    "/v1/dropbox-debug": dropbox_debug,
    "/v1/days-until": days_until_route,
}


def application(environ, start_response):
    route = routes.get(environ["PATH_INFO"])
    if not route:
        start_response("404 Not found", [("Content-type", "text/plain")])
        return ["Not found\n", environ["PATH_INFO"]]
    try:
        return route(environ, start_response)
    except Exception:
        start_response("500 Server error", [("Content-type", "text/plain")])
        return ["Server error\n", traceback.format_exc()]


def days_until(date_from, date_to):
    return (date_to - date_from).days + 1
