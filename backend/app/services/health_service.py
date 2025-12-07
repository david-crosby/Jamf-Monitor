from datetime import datetime, timedelta, timezone
from typing import Optional
from app.models.device import (
    DeviceHealth, DeviceBasicInfo, HealthCheckResult, 
    HealthStatus, HealthThresholds
)
from app.services.jamf_service import JamfAPIService
from app.core.config import get_settings
from functools import lru_cache
import asyncio

settings = get_settings()


class HealthCheckService:
    def __init__(self, jamf_service: JamfAPIService):
        self.jamf_service = jamf_service
        self.compliance_group_name = "Compliance"
        self.monitored_groups: list[str] = []
    
    def set_thresholds(
        self, 
        check_in_hours: Optional[int] = None,
        recon_hours: Optional[int] = None,
        pending_command_hours: Optional[int] = None
    ):
        if check_in_hours:
            settings.check_in_threshold_hours = check_in_hours
        if recon_hours:
            settings.recon_threshold_hours = recon_hours
        if pending_command_hours:
            settings.pending_command_threshold_hours = pending_command_hours
    
    def get_thresholds(self) -> HealthThresholds:
        return HealthThresholds(
            check_in_hours=settings.check_in_threshold_hours,
            recon_hours=settings.recon_threshold_hours,
            pending_command_hours=settings.pending_command_threshold_hours
        )
    
    async def check_device_health(self, computer_id: int) -> DeviceHealth:
        computer_detail = await self.jamf_service.get_computer_detail(computer_id)
        
        general = computer_detail.get("general", {})
        
        device_info = DeviceBasicInfo(
            id=computer_id,
            name=general.get("name", "Unknown"),
            serial_number=general.get("serialNumber", "Unknown"),
            model=general.get("modelIdentifier", "Unknown"),
            os_version=general.get("operatingSystemVersion", "Unknown"),
            last_contact_time=self._parse_jamf_date(general.get("lastContactTime")),
            last_inventory_update=self._parse_jamf_date(general.get("lastInventoryUpdateTimestamp"))
        )
        
        check_in_ok = self._check_recent_contact(device_info.last_contact_time)
        recon_ok = self._check_recent_recon(device_info.last_inventory_update)
        
        failed_policies = await self.jamf_service.get_failed_policies(computer_id)
        has_failed_policies = len(failed_policies) > 0
        
        mdm_commands = await self.jamf_service.get_mdm_commands(computer_id)
        has_failed_mdm = len(mdm_commands["failed"]) > 0
        has_pending_mdm = self._check_pending_commands(mdm_commands["pending"])
        
        group_memberships = await self.jamf_service.get_computer_group_membership(computer_id)
        is_compliant = self.compliance_group_name in group_memberships
        
        monitored_group_matches = [
            g for g in group_memberships 
            if g in self.monitored_groups and g != self.compliance_group_name
        ]
        
        health_result = HealthCheckResult(
            check_in_ok=check_in_ok,
            recon_ok=recon_ok,
            has_failed_policies=has_failed_policies,
            has_failed_mdm_commands=has_failed_mdm,
            has_pending_mdm_commands=has_pending_mdm,
            is_compliant=is_compliant,
            smart_group_memberships=monitored_group_matches
        )
        
        status = health_result.calculate_status()
        
        return DeviceHealth(
            device=device_info,
            health=health_result,
            status=status,
            last_checked=datetime.now(timezone.utc)
        )
    
    async def check_all_devices(self) -> list[DeviceHealth]:
        computers = await self.jamf_service.get_all_computers()
        
        tasks = [
            self.check_device_health(computer["id"]) 
            for computer in computers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if isinstance(r, DeviceHealth)]
    
    def _parse_jamf_date(self, date_string: Optional[str]) -> Optional[datetime]:
        if not date_string:
            return None
        
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _check_recent_contact(self, last_contact: Optional[datetime]) -> bool:
        if not last_contact:
            return False
        
        threshold = datetime.now(timezone.utc) - timedelta(
            hours=settings.check_in_threshold_hours
        )
        return last_contact > threshold
    
    def _check_recent_recon(self, last_recon: Optional[datetime]) -> bool:
        if not last_recon:
            return False
        
        threshold = datetime.now(timezone.utc) - timedelta(
            hours=settings.recon_threshold_hours
        )
        return last_recon > threshold
    
    def _check_pending_commands(self, pending_commands: list[dict]) -> bool:
        if not pending_commands:
            return False
        
        threshold = datetime.now(timezone.utc) - timedelta(
            hours=settings.pending_command_threshold_hours
        )
        
        for cmd in pending_commands:
            cmd_date = self._parse_jamf_date(cmd.get("dateIssued"))
            if cmd_date and cmd_date < threshold:
                return True
        
        return False


@lru_cache()
def get_health_service(jamf_service: JamfAPIService = None) -> HealthCheckService:
    from app.services.jamf_service import get_jamf_service
    if jamf_service is None:
        jamf_service = get_jamf_service()
    return HealthCheckService(jamf_service)
