# ServiceTitan MCP Server

> AI-native interface to ServiceTitan for home services contractors

An MCP (Model Context Protocol) server that gives AI assistants direct access to ServiceTitan — the leading field service management platform. Built for HVAC, plumbing, electrical, and other home services contractors who want their AI to manage jobs, look up customers, schedule appointments, dispatch technicians, and track invoices.

## 🛠️ Available Tools

| Tool | Description |
|------|-------------|
| `search_customers` | Search customers by name, phone, email, or address |
| `get_customer` | Get full customer details including contacts and service history |
| `list_jobs` | List jobs with filters for status, date range, customer, or technician |
| `get_job` | Get complete job details including notes and assigned tech |
| `create_job` | Create a new job for a customer |
| `get_available_appointments` | Find available appointment slots in a date range |
| `schedule_appointment` | Schedule or reschedule a job appointment |
| `list_technicians` | List active technicians with current status and schedule |
| `dispatch_technician` | Assign a technician to a job appointment |
| `get_invoice` | Get invoice details with line items and payment status |
| `list_unpaid_invoices` | List unpaid/overdue invoices for collections follow-up |

## 🚀 Quick Start

### 1. Get ServiceTitan API Credentials

1. Go to the [ServiceTitan Developer Portal](https://developer.servicetitan.io/)
2. Create an application in **My Apps** to get your **App Key**
3. Have your ServiceTitan admin generate **Client ID** and **Client Secret** for your environment
4. Note your **Tenant ID** from ServiceTitan settings

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials:
#   ST_CLIENT_ID=your_client_id
#   ST_CLIENT_SECRET=your_client_secret
#   ST_APP_KEY=your_app_key
#   ST_TENANT_ID=your_tenant_id
#   ST_ENVIRONMENT=production  # or "integration" for sandbox
```

### 3. Install & Run

```bash
# Install
pip install -e .

# Run the MCP server
servicetitan-mcp

# Or run directly
python -m servicetitan_mcp.server
```

### 4. Connect to Your AI

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "servicetitan": {
      "command": "servicetitan-mcp",
      "env": {
        "ST_CLIENT_ID": "your_client_id",
        "ST_CLIENT_SECRET": "your_client_secret",
        "ST_APP_KEY": "your_app_key",
        "ST_TENANT_ID": "your_tenant_id",
        "ST_ENVIRONMENT": "production"
      }
    }
  }
}
```

## 🔐 Authentication

ServiceTitan uses **OAuth2 Client Credentials** grant:

- **Auth endpoint**: `https://auth.servicetitan.io/connect/token` (production) or `https://auth-integration.servicetitan.io/connect/token` (sandbox)
- **API base**: `https://api.servicetitan.io` (production) or `https://api-integration.servicetitan.io` (sandbox)
- **Required headers**: `Authorization: Bearer {token}` + `ST-App-Key: {app_key}`
- Tokens are cached and auto-refreshed before expiry

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `ST_CLIENT_ID` | OAuth2 Client ID |
| `ST_CLIENT_SECRET` | OAuth2 Client Secret |
| `ST_APP_KEY` | ServiceTitan Application Key |
| `ST_TENANT_ID` | Your ServiceTitan Tenant ID |
| `ST_ENVIRONMENT` | `production` or `integration` (default: `production`) |

## 📦 ServiceTitan API Modules Used

| Module | Base Path | Entities |
|--------|-----------|----------|
| CRM | `/crm/v2/tenant/{id}/` | Customers, Contacts, Locations, Bookings |
| Job Planning | `/jpm/v2/tenant/{id}/` | Jobs, Appointments, Job Types |
| Dispatch | `/dispatch/v2/tenant/{id}/` | Technician Shifts, Appointment Assignments |
| Accounting | `/accounting/v2/tenant/{id}/` | Invoices, Payments |
| Settings | `/settings/v2/tenant/{id}/` | Technicians, Employees, Business Units |

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
```

## ☁️ Deployment

### Apify Marketplace

> Coming Day 3 — pay-per-event billing on Apify

The `apify_actor/` directory contains the deployment scaffold for the Apify platform.

### mcp.so

> Coming — listing at [mcp.so](https://mcp.so)

### Smithery

> Coming — listing at [smithery.ai](https://smithery.ai)

## 📋 Roadmap

- [x] **Day 1**: Core scaffold — 11 tools covering the contractor workflow loop
- [ ] **Day 2**: Validate against ServiceTitan sandbox, fix endpoint paths, add integration tests
- [ ] **Day 3**: Apify Actor deployment, pay-per-event billing, marketplace listings

## 📄 License

MIT
