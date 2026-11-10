# onward-orders-app

The Onward Logistics order system: a single Python application that serves
the web page and holds the order logic, packaged as one container image.

Merging to `main` is the only manual step in a release. The infrastructure
that runs it lives in a separate repository, `onward-orders-infra`.

## What is in this repository

| Path | What it is |
|---|---|
| `app/orders.py` | Order logic: creating orders and moving them through their statuses |
| `app/routes.py` | The web page, a small JSON API and the `/health` check |
| `app/templates/`, `app/static/` | The user interface |
| `app/config.py` | Name, lab name and version shown on the page |
| `tests/` | Tests for the logic and the pages |
| `Dockerfile` | Builds the single image |
| `deploy/taskdef.json` | How the container runs on ECS: CPU, memory, environment, health check |
| `deploy/appspec.yaml` | Tells CodeDeploy which container receives traffic |
| `.github/workflows/release.yml` | Tests every change; on `main`, builds and hands the release to AWS |

## Running it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
flask --app wsgi run --port 8080
```

Or as the container that runs in production:

```bash
docker build -t onward-orders .
docker run --rm -p 8080:8080 onward-orders
```

Then open http://localhost:8080.

## How a change reaches customers

1. Open a pull request. The tests run.
2. Merge to `main`. The workflow:
   - signs in to AWS with OIDC (no keys are stored anywhere),
   - builds the image and pushes it to ECR tagged with the commit,
   - uploads `taskdef.json` and `appspec.yaml` to S3 as the release bundle,
   - moves the `latest` tag to the new image.
3. Moving `latest` is the signal. EventBridge starts CodePipeline, and CodeDeploy performs a blue/green release: the new version starts beside the old one, takes 10% of traffic for five minutes, then all of it.
4. The footer of the page shows the running version (the commit), the task and the Availability Zone.

To change CPU, memory or environment variables, edit `deploy/taskdef.json` and merge. It is released the same way.

## Reversing a bad release

- **Automatically**: if the new version fails its health check or returns server errors during the release, CodeDeploy sends all traffic back to the old version.
- **By hand, within the rollback window**: stop the deployment in CodeDeploy and choose to roll back. The old version is still running, so this takes seconds.
- **Later**: revert the commit and merge. The revert is released like any other change.

## One-time setup

The workflow needs one repository variable. It is an identifier, not a credential:

```bash
gh variable set AWS_ACCOUNT_ID --body "$(aws sts get-caller-identity --query Account --output text)"
```

The Region and environment are set at the top of `.github/workflows/release.yml`.

## Good to know

- Re-running the workflow for a commit that was already released fails at the push: an image tag can never be overwritten. Push a new commit instead.
- Orders are kept in memory, per container. Each container has its own list and a release starts with the sample orders again. Storage is outside the scope of this lab.
