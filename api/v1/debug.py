import contextlib
import json
import urllib.parse


def app(environ, start_response):
    if environ["REQUEST_METHOD"] != "POST":
        start_response("200 OK", [("Content-type", "application/json")])
        return [json.dumps(urllib.parse.parse_qs(environ["QUERY_STRING"]), indent=2)]
    with contextlib.closing(environ["wsgi.input"]) as request_body_file:
        request_body = request_body_file.read(int(environ["CONTENT_LENGTH"]))
    start_response("200 OK", [("Content-type", "text/plain")])
    return [request_body]
