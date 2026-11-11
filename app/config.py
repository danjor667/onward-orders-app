"""Settings read from the environment, with defaults for local runs."""
import os

OWNER_NAME = os.environ.get("OWNER_NAME", "Jordan Steve")
LAB_NAME = os.environ.get(
    "LAB_NAME", "Delivering Order System Updates Safely for Onward Logistics"
)
# Set at build or install time to the Git commit, so every page shows which
# release served it.
APP_VERSION = os.environ.get("APP_VERSION", "local")

# Name of the DynamoDB table that holds the orders. When it is not set (a
# local run, the tests) orders are kept in memory instead.
ORDERS_TABLE = os.environ.get("ORDERS_TABLE")
AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

# Passcode for the Operations pages when running locally. On AWS the
# passcode is generated on first start and kept in the orders table: it is
# never in this repository. See the README.
LOCAL_STAFF_PASSCODE = os.environ.get("STAFF_PASSCODE", "onward-local")

# Rollback demonstration only. When "true", every page and API call fails
# with a 500 error while /health keeps answering, the kind of broken release
# a health check alone does not catch. The release pipeline must notice the
# errors and roll back. Off unless the task definition sets it.
SIMULATE_FAILURE = os.environ.get("SIMULATE_FAILURE", "false").lower() == "true"
