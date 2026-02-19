FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
COPY src/ src/
COPY apify_actor/ apify_actor/

RUN pip install --no-cache-dir .

# TODO (Day 3): Install apify SDK
# RUN pip install --no-cache-dir apify

EXPOSE 8000

# Run the MCP server
CMD ["python", "-m", "servicetitan_mcp.server"]
