from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    CAUTION = "caution"
    UNHEALTHY = "unhealthy"


class DeviceBasicInfo(BaseModel):
    id: int
    name: str
    serial_number: str
    model: str
    os_version: str
    last_contact_time: Optional[datetime] = None
    last_inventory_update: Optional[datetime] = None


class HealthCheckResult(BaseModel):
    check_in_ok: bool
    recon_ok: bool
    has_failed_policies: bool
    has_failed_mdm_commands: bool
    has_pending_mdm_commands: bool
    is_compliant: bool
    smart_group_memberships: list[str] = []
    
    def calculate_status(self) -> HealthStatus:
        if any([
            not self.check_in_ok,
            not self.recon_ok,
            self.has_failed_policies,
            self.has_failed_mdm_commands,
            self.has_pending_mdm_commands
        ]):
            return HealthStatus.UNHEALTHY
        
        if not self.is_compliant or self.smart_group_memberships:
            return HealthStatus.CAUTION
        
        return HealthStatus.HEALTHY


class DeviceHealth(BaseModel):
    device: DeviceBasicInfo
    health: HealthCheckResult
    status: HealthStatus
    last_checked: datetime


class DeviceListResponse(BaseModel):
    total: int
    devices: list[DeviceHealth]
    healthy_count: int
    caution_count: int
    unhealthy_count: int


class HealthThresholds(BaseModel):
    check_in_hours: int = Field(ge=1, le=168)
    recon_hours: int = Field(ge=1, le=168)
    pending_command_hours: int = Field(ge=1, le=72)


class JamfToken(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "Bearer"
