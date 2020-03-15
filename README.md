# Fructify

Webhooks to make me more productive. For use with IFTTT.

## Quick start

Frucitify is deployed to [ZEIT Now][now]. You can use the [CLI][cli] to run a
local version too.

Secrets are inserted as environment variables. You can see which secrets are
needed by looking in now.json. Put local secrets in a .env file.

Start a local server with `now dev`.

[now]: https://zeit.co/now
[cli]: https://zeit.co/download

## Contributing

To work on the application, you will need the dependencies. Make a new
virtualenv for this project before running the below commands because `pip-sync`
will remove unneeded dependencies.

```
pip install -r dev-requirements.txt
pip-sync dev-requirements.txt requirements.txt
```

Each .py file in the api directory is an endpoint. Each module defines a WSGI
application called app. Decorate the app with `fructify.tracing.with_tracing` to
instrument it.

Run tests with `tox`. Lint code with `flake8`. Format code with `black .`.

Think carefully before adding new dependencies, and only consider well used
packages. Dependencies introduce risk and need to be kept up to date. If you add
application dependencies, add them to setup.py and follow the instructions
inside requirements.txt to update it. If you add a development dependency, add
it to dev-requirements.in and follow the instructions inside
dev-requirements.txt to update it. Use ~= notation to define the major and
minimum minor versions and let pip-tools decide a patch version.

Talk to the maintainer before making a pull request to make sure what you are
adding is wanted. The build will check tests, linting, formatting, and
dependencies. Consider running these yourself before making a pull request.

This project uses the Apache License 2.0. You will be credited in the git
history, but for ease of maintenance copyright stays with the maintainer.

Each push to master is deployed.
