FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vault_server.py mcp_server.py ./

# Firebase service account is mounted at runtime
# FIREBASE_CREDENTIALS=/app/service_account.json

EXPOSE 8003 8004

# Default: run both REST API and MCP server
CMD ["sh", "-c", "python vault_server.py & python mcp_server.py"]
