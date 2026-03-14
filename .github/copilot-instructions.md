# Repository Custom Instructions

## Before Considering Work Finished

All status checks must be green on the latest commit before the work is done.

### Circle CI (Python & JavaScript)

Circle CI runs the build with tests, linting, and other checks. It is **not** a
GitHub Action — check the statuses reported directly on the commit.

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

#### Reading Circle CI Logs

`circleci.com` is **not** reachable via Playwright in the agent sandbox, but the
Circle CI REST API is reachable via `curl`. Use this approach when a build fails:

1. Get the build number from the commit status `target_url` using the
   `github-mcp-server-pull_request_read` tool with `method: get_status`. The URL
   looks like `https://circleci.com/gh/{org}/{repo}/543` — the build number
   is the last path segment (`543`).

2. Fetch build details to find failing steps and their log URLs:
   ```bash
   curl -s "https://circleci.com/api/v1.1/project/github/{org}/{repo}/{build_number}" \
     | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   print('status:', d['status'])
   for s in d.get('steps', []):
       for a in s.get('actions', []):
           if a['status'] != 'success':
               print(a['name'], a['status'], a.get('output_url'))
   "
   ```

3. Fetch the log output via the presigned `output_url` from the step:
   ```bash
   curl -s "{output_url}" | python3 -c "
   import json, sys
   for msg in json.load(sys.stdin):
       print(msg.get('message', ''), end='')
   "
   ```

Alternatively, use the v2 API to navigate pipeline → workflow → jobs by branch:
```bash
# 1. Find the pipeline for the branch
curl -s "https://circleci.com/api/v2/project/github/{org}/{repo}/pipeline?branch={branch}"
# 2. Get workflows for the pipeline
curl -s "https://circleci.com/api/v2/pipeline/{pipeline_id}/workflow"
# 3. Get jobs (includes job_number used by v1.1 for log retrieval)
curl -s "https://circleci.com/api/v2/workflow/{workflow_id}/job"
```

### Vercel (Preview Deployment)

Vercel builds a preview deployment and reports its status on the commit.

`vercel.com` and `*.vercel.app` are reachable via `curl` and the Vercel CLI
from the agent sandbox, but **not** via Playwright. To check the deployment
status without a browser, read the Vercel bot comment on the PR using
`github-mcp-server-pull_request_read` with `method: get_comments`. Look for the
comment from `vercel[bot]` — it contains a Markdown table with a **Preview**
link and the deployment status (e.g. "Ready").

#### Verifying the app locally with the Vercel CLI

To actually exercise the app (check the build works and the login link is
offered), use the Vercel CLI to run the app locally. The `VERCEL_TOKEN`
environment variable is available in the agent sandbox.

1. **Install prerequisites:**
   ```bash
   npm install -g vercel
   pip install uv   # required by vercel build for Python functions
   ```

2. **Link and pull environment variables:**
   ```bash
   # Link the project and pull developer env vars (includes HONEYCOMB_KEY)
   vercel link --non-interactive --scope fergal-hainey-s-team --project fructify --yes --token "$VERCEL_TOKEN"
   ```
   This creates `.env.local` with the developer secrets (including `HONEYCOMB_KEY`),
   and automatically adds `.env.local` to `.gitignore`.

3. **Check the build works** (optional but useful to confirm a build change is
   sound before waiting for CI):
   ```bash
   vercel build --token "$VERCEL_TOKEN"
   # Succeeds with: ✅  Build Completed in .vercel/output
   ```

4. **Run the app locally** — `vercel dev` has a CLI bug that causes it to crash
   after the Next.js build step, so instead run the two services separately.
   The `next.config.js` proxies `/api/...` to Flask on port 5000 in development:
   ```bash
   # Terminal 1: start the Flask Python API
   set -a && source .env.local && set +a
   python3 -m flask --app api/index.py run --port 5000

   # Terminal 2: start the Next.js frontend
   npm run dev -- --port 3000
   ```
   Or as background processes in a single shell:
   ```bash
   set -a && source .env.local && set +a
   python3 -m flask --app api/index.py run --port 5000 > /tmp/flask.log 2>&1 &
   npm run dev -- --port 3000 > /tmp/nextjs.log 2>&1 &
   ```

5. **Check the login offer with Playwright** — once both servers are up
   (`curl http://localhost:5000/api/v1/authcheck` returns `{"loggedIn":false}`
   and `curl http://localhost:3000/` returns HTML), navigate to the app:
   ```js
   // Playwright: navigate and wait for login link
   await page.goto('http://localhost:3000');
   await page.getByText('Log in').first().waitFor({ state: 'visible' });
   // Should see: <a href="/api/v1/login">Log in/Sign up</a>
   ```
   `http://localhost:3000` **is** reachable via Playwright in the agent sandbox.

   ![Login offer screenshot](https://github.com/user-attachments/assets/c5f402bc-6f68-4739-b8d9-e4b04f085a8a)

6. **Verify Honeycomb tracing** — the `HONEYCOMB_KEY` from `.env.local`
   is used by the Flask app to publish traces to Honeycomb. On non-Classic Honeycomb
   Environments, data routes to a dataset named after the service (`"fructify"`), not
   the `x-honeycomb-dataset` header. The production environment is classic, and local
   dev is non-classic. After browsing the local app (step 5), confirm that spans
   reached Honeycomb using the **Honeycomb MCP server** (available as a native MCP tool
   in agent sessions). Call the `run_query` tool with these arguments:
   ```json
   {
     "environment_slug": "copilotlocal",
     "dataset_slug": "fructify",
     "query_spec": {
       "calculations": [{"op": "COUNT"}],
       "breakdowns": ["http.target"],
       "filters": [{"column": "service.name", "op": "=", "value": "fructify"}],
       "time_range": 600
     }
   }
   ```
   This should return a results table like:
   ```
   | COUNT | http.target |
   | --- | --- |
   | 6 | /api/v1/authcheck |
   ```
   Each page request in step 5 produces at least one span. Results are broken down by
   `http.target`, so browsing different pages shows distinct URLs with their span counts.

   If you cannot see data in Honeycomb, check these common causes in order:

   1. **`HONEYCOMB_KEY` is empty** — confirm the key is non-empty after sourcing `.env.local`:
      ```bash
      env | grep HONEYCOMB
      ```
      `vercel env pull .env.local` should have populated it as a developer-type variable.
      If still empty, re-run `vercel env pull .env.local --yes --token "$VERCEL_TOKEN"`.
   2. **`api.honeycomb.io` is unreachable** — confirm connectivity:
      ```bash
      curl -s "https://api.honeycomb.io/1/auth" -H "X-Honeycomb-Team: $HONEYCOMB_KEY"
      # Valid key → {"api_key_access":...}  |  blocked → curl: (6) Could not resolve host
      ```
   3. **OpenTelemetry export errors appear in Flask output** — the OTel SDK logs export
      failures as Python `WARNING`-level messages, which Flask's development server
      forwards to its output (stdout/stderr). If spans are not arriving, run Flask
      interactively (not in background) and look for lines like
      `Failed to export batch code: ...` or HTTP error responses from
      `api.honeycomb.io`. The most common cause is an incorrect or empty `HONEYCOMB_KEY`
      (check step 1). Note that the dataset `"fructify"` is created automatically on
      first use — it will not exist in Honeycomb until the first successful export.

### Fixing Failures

Fix any problems found in the status checks on the latest commit. Keep
iterating until all checks are green or until you are stuck and need to ask for
help.

Do **not** assume that a locally passing run guarantees the same result in CI.
Always wait for the actual commit statuses.
