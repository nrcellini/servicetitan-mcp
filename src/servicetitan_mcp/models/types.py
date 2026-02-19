"""Pydantic models for ServiceTitan API entities and configuration.

These models represent the core ServiceTitan objects used across
the MCP tools. Fields use Optional liberally since the API may
omit fields depending on the endpoint or permissions.

TODO (Day 2): Validate these field names against the actual ST
sandbox responses and adjust as needed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class ServiceTitanConfig(BaseSettings):
    """ServiceTitan API configuration loaded from environment variables."""

    client_id: str = Field(alias="ST_CLIENT_ID")
    client_secret: str = Field(alias="ST_CLIENT_SECRET")
    app_key: str = Field(alias="ST_APP_KEY")
    tenant_id: str = Field(alias="ST_TENANT_ID")
    environment: str = Field(default="production", alias="ST_ENVIRONMENT")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "populate_by_name": True}


# ---------------------------------------------------------------------------
# CRM Models
# ---------------------------------------------------------------------------

class CustomerContact(BaseModel):
    """A phone/email contact on a customer record."""
    id: Optional[int] = None
    type: Optional[str] = None  # Phone, Email, Fax
    value: Optional[str] = None
    memo: Optional[str] = None


class Location(BaseModel):
    """A service location (address)."""
    id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None  # TODO: may be nested object (street, city, state, zip, country)
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    customerId: Optional[int] = None


class Customer(BaseModel):
    """A ServiceTitan customer record."""
    id: Optional[int] = None
    active: Optional[bool] = None
    name: Optional[str] = None
    type: Optional[str] = None  # Residential, Commercial
    address: Optional[dict[str, Any]] = None
    customFields: Optional[list[dict[str, Any]]] = None
    balance: Optional[float] = None
    doNotMail: Optional[bool] = None
    doNotService: Optional[bool] = None
    createdOn: Optional[datetime] = None
    modifiedOn: Optional[datetime] = None
    memberships: Optional[list[dict[str, Any]]] = None
    hasActiveMembership: Optional[bool] = None
    contacts: Optional[list[CustomerContact]] = None
    phoneSettings: Optional[list[dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# Job Planning & Management Models
# ---------------------------------------------------------------------------

class JobNote(BaseModel):
    """A note attached to a job."""
    id: Optional[int] = None
    text: Optional[str] = None
    createdOn: Optional[datetime] = None
    createdById: Optional[int] = None


class Job(BaseModel):
    """A ServiceTitan job record."""
    id: Optional[int] = None
    jobNumber: Optional[str] = None
    customerId: Optional[int] = None
    locationId: Optional[int] = None
    jobStatus: Optional[str] = None  # Scheduled, InProgress, Completed, Canceled, etc.
    jobTypeId: Optional[int] = None
    jobTypeName: Optional[str] = None
    priority: Optional[str] = None
    campaignId: Optional[int] = None
    businessUnitId: Optional[int] = None
    summary: Optional[str] = None
    createdOn: Optional[datetime] = None
    modifiedOn: Optional[datetime] = None
    completedOn: Optional[datetime] = None
    scheduledOn: Optional[datetime] = None  # TODO: verify field name
    totalAmount: Optional[float] = None
    customerName: Optional[str] = None
    locationName: Optional[str] = None


class Appointment(BaseModel):
    """A scheduled appointment within a job."""
    id: Optional[int] = None
    jobId: Optional[int] = None
    appointmentNumber: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    arrivalWindowStart: Optional[datetime] = None
    arrivalWindowEnd: Optional[datetime] = None
    status: Optional[str] = None  # Scheduled, Dispatched, Working, Done, Canceled
    technicianIds: Optional[list[int]] = None  # TODO: verify — might be nested assignments
    specialInstructions: Optional[str] = None
    createdOn: Optional[datetime] = None
    modifiedOn: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Dispatch / Settings Models
# ---------------------------------------------------------------------------

class Technician(BaseModel):
    """A ServiceTitan technician (from settings/employees with tech role)."""
    id: Optional[int] = None
    name: Optional[str] = None
    active: Optional[bool] = None
    email: Optional[str] = None
    phoneNumber: Optional[str] = None
    businessUnitId: Optional[int] = None
    # Dispatch-specific fields (from dispatch endpoints)
    status: Optional[str] = None  # TODO: available/on-job/driving — may come from dispatch/technician-shifts


# ---------------------------------------------------------------------------
# Accounting / Invoice Models
# ---------------------------------------------------------------------------

class InvoiceItem(BaseModel):
    """A line item on an invoice."""
    id: Optional[int] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unitPrice: Optional[float] = None
    totalPrice: Optional[float] = None
    skuName: Optional[str] = None
    skuId: Optional[int] = None
    type: Optional[str] = None  # Service, Material, Equipment


class Invoice(BaseModel):
    """A ServiceTitan invoice."""
    id: Optional[int] = None
    jobId: Optional[int] = None
    invoiceNumber: Optional[str] = None
    customerId: Optional[int] = None
    status: Optional[str] = None  # Pending, Exported, Posted
    total: Optional[float] = None
    subTotal: Optional[float] = None
    taxAmount: Optional[float] = None
    balance: Optional[float] = None  # Remaining unpaid amount
    dueDate: Optional[datetime] = None
    createdOn: Optional[datetime] = None
    modifiedOn: Optional[datetime] = None
    items: Optional[list[InvoiceItem]] = None
    customerName: Optional[str] = None


# ---------------------------------------------------------------------------
# Generic paginated response
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel):
    """Standard ServiceTitan paginated API response wrapper."""
    page: Optional[int] = None
    pageSize: Optional[int] = None
    totalCount: Optional[int] = None
    hasMore: Optional[bool] = None
    data: Optional[list[dict[str, Any]]] = None
