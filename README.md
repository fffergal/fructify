# Fructify

Webhooks to make me more productive. For use with IFTTT.

## Quick start

Secrets are inserted as environment variables. You can see which secrets are
needed by looking in vercel.json. Put local secrets in a .env file. If you have
access to LastPass and the lpass CLI installed, you can use make_env.sh to make
the .env file.

To work on the application, you will need the dependencies. Make a new
virtualenv for this project before running the below commands because `pip-sync`
will remove unneeded dependencies.

```
pip install -r dev-requirements.txt
pip-sync dev-requirements.txt requirements.txt
```

Install frontend dependencies with `npm ci`.

Run `npm run dev` to start the frontend, and `flask --app api.index --debug` in
a different shell to start the backend. You can now use the local version at
http://localhost:3000.

## Contributing

Vercel can make a separate Lambda for every file in the api directory, but this
project uses a single Flask app in api/index.py imported from the fructify
package.

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

Frucitify is deployed to [Vercel][vercel], every merge to master is deployed
to https://fructify.app, and each PR has preview.

[vercel]: https://vercel.com/
