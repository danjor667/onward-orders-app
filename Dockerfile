# One image holds the user interface and the order logic.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wsgi.py .
COPY app ./app

# Run as an unprivileged user.
RUN useradd --system --no-create-home onward
USER onward

# The release workflow passes the Git commit so each page shows its version.
ARG APP_VERSION=local
ENV APP_VERSION=${APP_VERSION}

EXPOSE 8080

# One worker so all requests to this container see the same in-memory
# orders; threads handle concurrency. Scaling happens by adding containers.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--access-logfile", "-", "wsgi:app"]
