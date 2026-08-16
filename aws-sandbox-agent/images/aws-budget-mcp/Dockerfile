# AWS budget/capacity MCP tools (us-east-2, read-mostly).
# Intended tags:
#   aws-budget-mcp:dev                         (local / ctr images import)
#   ghcr.io/sebbycorp/aws-budget-mcp:dev       (published name; not required)
#
# STREAMABLE_HTTP on :8084 /mcp — same shape as kagent-tool-server
# and fortigate-mcp. Credentials come from env (K8s Secret via
# ExternalSecret). Do not bake secrets in.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8084 \
    AWS_DEFAULT_REGION=us-east-2 \
    AWS_EC2_METADATA_DISABLED=true

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
