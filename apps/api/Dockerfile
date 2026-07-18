# AirSpaceSim API image (build context: repository root).
#
#   docker build -f apps/api/Dockerfile -t airspacesim-api .
#
# The container applies Alembic migrations and then serves uvicorn
# (see apps/api/docker-entrypoint.sh). PaaS platforms that build from a
# Dockerfile can use this directly; the same image runs in docker-compose.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv/airspacesim

# Engine package first (its own layer for caching).
COPY pyproject.toml MANIFEST.in README.md LICENSE requirements.txt ./
COPY airspacesim/ airspacesim/
RUN pip install --no-cache-dir .

# Hosted API with the PostgreSQL driver.
COPY apps/api/ apps/api/
RUN pip install --no-cache-dir "./apps/api[postgres]"

# Content served by the API (airspace packages + curriculum).
COPY airspaces/ airspaces/
COPY content/ content/

COPY apps/api/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /srv/airspacesim/apps/api
EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
