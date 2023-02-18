from werkzeug.middleware.proxy_fix import ProxyFix

from fructify.app import create_app


app = create_app()

if app.config["DEBUG"]:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
