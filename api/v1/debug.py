from flask import Flask, request
from fructify.tracing import with_flask_tracing


app = with_flask_tracing(Flask(__name__))


@app.route("/api/v1/debug", methods=["DELETE", "GET", "POST"])
def debug():
    if request.method == "DELETE":
        raise Exception
    if request.method != "POST":
        return request.args
    return request.get_data()
