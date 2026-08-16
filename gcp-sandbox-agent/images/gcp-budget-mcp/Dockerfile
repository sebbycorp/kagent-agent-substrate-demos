# GCP budget/capacity MCP tools (us-east1, read-mostly).
# Intended tags:
#   gcp-budget-mcp:dev                         (local / ctr images import)
#   ghcr.io/sebbycorp/gcp-budget-mcp:dev       (published name; not required)
#
# STREAMABLE_HTTP on :8084 /mcp — same shape as kagent-tool-server
# and aws-budget-mcp. Credentials come from env / mounted SA JSON
# (K8s Secret via ExternalSecret). Do not bake secrets in.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8084 \
    GCP_REGION=us-east1

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin mcp

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && rm -rf /root/.cache/pip

COPY --chown=mcp:mcp server.py /app/server.py

USER 1000:1000
EXPOSE 8084
CMD ["python", "/app/server.py"]
