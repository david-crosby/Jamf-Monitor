from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import (
    DeviceHealth, DeviceBasicInfo, HealthCheckResult, 
    HealthStatus, HealthThresholds
)
from app.services.jamf_service import JamfAPIService
from app.core.config import get_settings
from app.core.repositories import SettingsRepository, DeviceCacheRepository
import asyncio

settings = get_settings()


class HealthCheckService:
    """
    Service for checking device health with database caching support.
    """
    
    def __init__(self, jamf_service: JamfAPIService, db_session: Optional[AsyncSession] = None):
        self.jamf_service = jamf_service
        self.db_session = db_session
        self._settings_repo: Optional[SettingsRepository] = None
        self._cache_repo: Optional[DeviceCacheRepository] = None
        
        # Fallback to in-memory storage if no database session
        self._compliance_group_name = "Compliance"
        self._monitored_groups: list[str] = []
    
    @property
    def settings_repo(self) -> Optional[SettingsRepository]:
        """
        Lazy initialisation of settings repository.
        """
        if self.db_session and not self._settings_repo:
            self._settings_repo = SettingsRepository(self.db_session)
        return self._settings_repo
    
    @property
    def cache_repo(self) -> Optional[DeviceCacheRepository]:
        """
        Lazy initialisation of cache repository.
        """
        if self.db_session and not self._cache_repo:
            self._cache_repo = DeviceCacheRepository(self.db_session)
        return self._cache_repo
    
    async def get_thresholds(self) -> HealthThresholds:
        """
        Get health check thresholds from database or defaults.
        """
        if self.settings_repo:
            db_thresholds = await self.settings_repo.get_health_thresholds()
            if db_thresholds:
                return HealthThresholds(
                    check_in_hours=db_thresholds.check_in_hours,
                    recon_hours=db_thresholds.recon_hours,
                    pending_command_hours=db_thresholds.pending_command_hours
                )
        
        return HealthThresholds(
            check_in_hours=settings.check_in_threshold_hours,
            recon_hours=settings.recon_threshold_hours,
            pending_command_hours=settings.pending_command_threshold_hours
        )
    
    async def set_thresholds(
        self, 
        check_in_hours: Optional[int] = None,
        recon_hours: Optional[int] = None,
        pending_command_hours: Optional[int] = None
    ) -> None:
        """
        Update health check thresholds.
        """
        current = await self.get_thresholds()
        
        new_check_in = check_in_hours if check_in_hours is not None else current.check_in_hours
        new_recon = recon_hours if recon_hours is not None else current.recon_hours
        new_pending = (
            pending_command_hours 
            if pending_command_hours is not None 
            else current.pending_command_hours
        )
        
        if self.settings_repo:
            await self.settings_repo.update_health_thresholds(
                check_in_hours=new_check_in,
                recon_hours=new_recon,
                pending_command_hours=new_pending
            )
        else:
            # Fallback to environment settings
            settings.check_in_threshold_hours = new_check_in
            settings.recon_threshold_hours = new_recon
            settings.pending_command_threshold_hours = new_pending
    
    async def get_compliance_group_name(self) -> str:
        """
        Get the compliance group name.
        """
        if self.settings_repo:
            return await self.settings_repo.get_compliance_group()
        return self._compliance_group_name
    
    async def set_compliance_group_name(self, name: str) -> None:
        """
        Set the compliance group name.
        """
        if self.settings_repo:
            await self.settings_repo.set_compliance_group(name)
        else:
            self._compliance_group_name = name
    
    async def get_monitored_groups(self) -> list[str]:
        """
        Get the list of monitored groups.
        """
        if self.settings_repo:
            return await self.settings_repo.get_monitored_groups()
        return self._monitored_groups
    
    async def set_monitored_groups(self, groups: list[str]) -> None:
        """
        Set the list of monitored groups.
        """
        if self.settings_repo:
            await self.settings_repo.set_monitored_groups(groups)
        else:
            self._monitored_groups = groups
    
    async def check_device_health(
        self, 
        computer_id: int,
        use_cache: bool = True
    ) -> DeviceHealth:
        """
        Check device health, using cache if available and not expired.
        """
        if use_cache and self.cache_repo:
            cached = await self.cache_repo.get_cached_device(computer_id)
            if cached:
                return self._device_health_from_cache(cached)
        
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
        
        thresholds = await self.get_thresholds()
        
        check_in_ok = self._check_recent_contact(
            device_info.last_contact_time, 
            thresholds.check_in_hours
        )
        recon_ok = self._check_recent_recon(
            device_info.last_inventory_update,
            thresholds.recon_hours
        )
        
        failed_policies = await self.jamf_service.get_failed_policies(computer_id)
        has_failed_policies = len(failed_policies) > 0
        
        mdm_commands = await self.jamf_service.get_mdm_commands(computer_id)
        has_failed_mdm = len(mdm_commands["failed"]) > 0
        has_pending_mdm = self._check_pending_commands(
            mdm_commands["pending"],
            thresholds.pending_command_hours
        )
        
        group_memberships = await self.jamf_service.get_computer_group_membership(computer_id)
        compliance_group = await self.get_compliance_group_name()
        is_compliant = compliance_group in group_memberships
        
        monitored_groups = await self.get_monitored_groups()
        monitored_group_matches = [
            g for g in group_memberships 
            if g in monitored_groups and g != compliance_group
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
        
        device_health = DeviceHealth(
            device=device_info,
            health=health_result,
            status=status,
            last_checked=datetime.now(timezone.utc)
        )
        
        if self.cache_repo:
            await self.cache_repo.cache_device_health(
                device_health,
                ttl_seconds=settings.cache_ttl_seconds
            )
        
        return device_health
    
    async def check_all_devices(self, use_cache: bool = True) -> list[DeviceHealth]:
        """
        Check health for all devices, using cache where available.
        """
        computers = await self.jamf_service.get_all_computers()
        
        results = []
        errors = []
        
        for computer in computers:
            try:
                device_health = await self.check_device_health(
                    computer["id"],
                    use_cache=use_cache
                )
                results.append(device_health)
            except Exception as e:
                errors.append({
                    "device_id": computer["id"],
                    "error": str(e)
                })
        
        if errors:
            print(f"Failed to check {len(errors)} devices: {errors}")
        
        return results
    
    def _device_health_from_cache(self, cached) -> DeviceHealth:
        """
        Convert cached database entry to DeviceHealth model.
        """
        device_info = DeviceBasicInfo(
            id=cached.device_id,
            name=cached.device_name,
            serial_number=cached.serial_number,
            model=cached.model,
            os_version=cached.os_version,
            last_contact_time=cached.last_contact_time,
            last_inventory_update=cached.last_inventory_update
        )
        
        health_result = HealthCheckResult(
            check_in_ok=cached.check_in_ok,
            recon_ok=cached.recon_ok,
            has_failed_policies=cached.has_failed_policies,
            has_failed_mdm_commands=cached.has_failed_mdm_commands,
            has_pending_mdm_commands=cached.has_pending_mdm_commands,
            is_compliant=cached.is_compliant,
            smart_group_memberships=cached.smart_group_memberships or []
        )
        
        return DeviceHealth(
            device=device_info,
            health=health_result,
            status=HealthStatus(cached.status),
            last_checked=cached.cached_at
        )
    
    def _parse_jamf_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """
        Parse Jamf date strings to datetime objects.
        """
        if not date_string:
            return None
        
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _check_recent_contact(
        self, 
        last_contact: Optional[datetime],
        threshold_hours: int
    ) -> bool:
        """
        Check if device has contacted recently within threshold.
        """
        if not last_contact:
            return False
        
        threshold = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
        return last_contact > threshold
    
    def _check_recent_recon(
        self,
        last_recon: Optional[datetime],
        threshold_hours: int
    ) -> bool:
        """
        Check if device has run recon recently within threshold.
        """
        if not last_recon:
            return False
        
        threshold = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
        return last_recon > threshold
    
    def _check_pending_commands(
        self,
        pending_commands: list[dict],
        threshold_hours: int
    ) -> bool:
        """
        Check if there are pending commands older than threshold.
        """
        if not pending_commands:
            return False
        
        threshold = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
        
        for cmd in pending_commands:
            cmd_date = self._parse_jamf_date(cmd.get("dateIssued"))
            if cmd_date and cmd_date < threshold:
                return True
        
        return False
