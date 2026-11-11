# onward-orders-app

The Onward Logistics order system: customers book and track parcel
deliveries, staff run them from a dashboard. A single Python application
serves the pages and holds the order logic, packaged as one container image.

Merging to `main` is the only manual step in a release. The infrastructure
that runs it lives in a separate repository, `onward-orders-infra`.

## What is in this repository

| Path | What it is |
|---|---|
| `app/pricing.py` | What a delivery costs and how long it takes: route × parcel size × speed |
| `app/orders.py` | The rules for placing, moving and cancelling an order |
| `app/store.py` | Where orders are kept: in memory locally, in DynamoDB on AWS |
| `app/stats.py` | Numbers and search for the operations dashboard |
| `app/security.py` | Form tokens and the staff passcode |
| `app/runtime.py` | Which container or server answered, shown on every page |
| `app/web/` | The pages: `customer.py` (book, track, cancel), `ops.py` (staff dashboard), `api.py` (JSON API and `/health`) |
| `app/templates/`, `app/static/` | The user interface |
| `tests/` | Tests for each of the above. DynamoDB is simulated, so no AWS account is needed |
| `Dockerfile` | Builds the single image |
| `deploy/taskdef.json` | How the container runs on ECS: CPU, memory, environment, health check |
| `deploy/appspec.yaml` | Tells CodeDeploy which container receives traffic |
| `.github/workflows/release.yml` | Tests every change; on `main`, builds and hands the release to AWS |

## What the application does

**Customers and merchants**

- Book a delivery in three steps: route, parcel, people. The price updates as they choose.
- Get a tracking code (for example `ONW-7KQ2MX`) and follow the parcel on a timeline, with an estimated delivery time.
- Cancel an order until a rider has picked it up.
- See their recent orders on the home page.

**Riders and staff** (the *Operations* link, behind a passcode)

- A dashboard: orders in progress, placed and delivered today, revenue, orders by status.
- Search and filter orders, move a parcel to its next step, cancel an order.

Two sample orders always exist, `ONW-DEMO01` and `ONW-DEMO02`, so tracking can be shown straight away.

### The staff passcode

- **Locally** it is `onward-local` (or the `STAFF_PASSCODE` environment variable).
- **On AWS** it is generated the first time the application starts and kept in the orders table, so it is never in this repository. Read it with AWS credentials:

  ```bash
  aws dynamodb get-item --table-name onward-dev-orders \
    --key '{"pk":{"S":"CONFIG"}}' --query Item.staff_passcode.S --output text
  ```

  To change it, delete that item and restart the application.

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

Then open http://localhost:8080. Locally, orders are kept in memory and are lost when the application stops.

## How a change reaches customers

1. Open a pull request. The tests run.
2. Merge to `main`. The workflow:
   - signs in to AWS with OIDC (no keys are stored anywhere),
   - builds the image and pushes it to ECR tagged with the commit,
   - uploads `taskdef.json` and `appspec.yaml` to S3 as the release bundle,
   - moves the `latest` tag to the new image.
3. Moving `latest` is the signal. EventBridge starts CodePipeline, and CodeDeploy performs a blue/green release: the new version starts beside the old one, takes 10% of traffic for five minutes, then all of it.
4. The footer of every page shows which task answered, its Availability Zone and the running version (the commit).

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
- On AWS, orders live in a DynamoDB table shared by every container, so they survive releases and scaling. The table name reaches the container through `ORDERS_TABLE` in `deploy/taskdef.json`.
- The Operations passcode travels over plain HTTP until the load balancer has a certificate. Real staff sign-in (for example Amazon Cognito) is the next step.
- Anyone who knows a tracking code can view or cancel that order, as with most courier tracking links.
