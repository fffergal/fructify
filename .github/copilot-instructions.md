# Repository Custom Instructions

## Before Considering Work Finished

All status checks must be green on the latest commit before the work is done.

### Circle CI (Python & JavaScript)

Circle CI runs the build with tests, linting, and other checks. It is **not** a
GitHub Action — check the statuses reported directly on the commit.

If Circle CI fails, follow the link from the commit status to see the logs.
Visit it with Playwright and search for the failing step to extract the relevant
logs.

The CI runs two jobs (see `.circleci/config.yml` for the authoritative config):

**`test_python`** (Python 3.12):
- `pip install -r dev-requirements.txt`
- `black --check .` — formatting check
- `flake8` — linting
- `tox` — runs the test suite
- `pip-compile --no-annotate --no-emit-index-url` — checks `requirements.txt` is up to date
- `pip-compile --no-annotate --no-emit-index-url dev-requirements.in` — checks `dev-requirements.txt` is up to date
- `git diff --exit-code -- dev-requirements.txt requirements.txt` — ensures compiled requirement files were committed

**`test_javascript`** (Node 22):
- `npm ci`
- `npm run lint`

For faster local iteration, run the same commands locally using the pinned
dependency versions from `dev-requirements.txt` / `package-lock.json`. But
always wait for the real Circle CI status on the commit — a local pass does not
guarantee a CI pass.

### Vercel (Preview Deployment)

Vercel builds a preview deployment and reports its status on the commit.

- If the build fails, you may not have permission to view the logs. Ask the
  repository owner for the logs if needed.
- Once the preview URL is available, visit it with Playwright and wait for it to
  offer the login link after checking login status. Preview deployments do not
  have login enabled, but waiting for that check to complete exercises both the
  Python API and JavaScript frontend.
  - If the page fails to load or takes too long, ask for the access logs to
    diagnose the error.

### Fixing Failures

Fix any problems found in the status checks on the latest commit. Keep
iterating until all checks are green or until you are stuck and need to ask for
help.

Do **not** assume that a locally passing run guarantees the same result in CI.
Always wait for the actual commit statuses.
