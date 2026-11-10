"""Settings read from the environment, with defaults for local runs."""
import os

OWNER_NAME = os.environ.get("OWNER_NAME", "Jordan Steve")
LAB_NAME = os.environ.get(
    "LAB_NAME", "Delivering Order System Updates Safely for Onward Logistics"
)
# Set at image build time to the Git commit, so every page shows which
# release served it.
APP_VERSION = os.environ.get("APP_VERSION", "local")
