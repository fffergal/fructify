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

- If the build fails, you may not have permission to view the logs. Ask the
  repository owner for the logs if needed.
- Once the preview URL is available, visit it with Playwright and wait for it to
  offer the login link after checking login status. Preview deployments do not
  have login enabled, but waiting for that check to complete exercises both the
  Python API and JavaScript frontend.
  - If the page fails to load or takes too long, ask for the access logs to
    diagnose the error.

#### Finding the Vercel Preview URL

`vercel.com` and `*.vercel.app` preview URLs are **not** reachable via
Playwright or `curl` from the agent sandbox. To find the preview URL and check
the deployment status without a browser:

1. Read the Vercel bot comment on the PR using
   `github-mcp-server-pull_request_read` with `method: get_comments`. Look for
   the comment from `vercel[bot]` — it contains a Markdown table with a
   **Preview** link and the deployment status (e.g. "Ready").

2. The preview URL follows the pattern:
   `https://{project}-git-{branch-slug}-{team}.vercel.app`

3. Because the preview domain is not reachable from the sandbox, confirming the
   login check requires Playwright in an environment that can reach `vercel.app`.
   If that is not available, rely on the Vercel bot comment status ("Ready") as
   confirmation that the deployment succeeded.

### Fixing Failures

Fix any problems found in the status checks on the latest commit. Keep
iterating until all checks are green or until you are stuck and need to ask for
help.

Do **not** assume that a locally passing run guarantees the same result in CI.
Always wait for the actual commit statuses.
