from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import json

from app.core.db_models import (
    ApplicationSettings,
    HealthThreshold,
    CachedDeviceHealth,
    User
)
from app.models.device import HealthThresholds, DeviceHealth


class SettingsRepository:
    """
    Repository for managing application settings in the database.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_setting(self, key: str) -> Optional[str]:
        """
        Retrieve a setting value by key.
        """
        result = await self.session.execute(
            select(ApplicationSettings).where(ApplicationSettings.setting_key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.setting_value if setting else None

    async def set_setting(self, key: str, value: str) -> None:
        """
        Set or update a setting value.
        """
        result = await self.session.execute(
            select(ApplicationSettings).where(ApplicationSettings.setting_key == key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.now(timezone.utc)
        else:
            setting = ApplicationSettings(setting_key=key, setting_value=value)
            self.session.add(setting)

        await self.session.flush()

    async def get_health_thresholds(self) -> Optional[HealthThreshold]:
        """
        Get the active health thresholds.
        """
        result = await self.session.execute(
            select(HealthThreshold)
            .where(HealthThreshold.is_active == True)
            .order_by(HealthThreshold.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def update_health_thresholds(
        self,
        check_in_hours: int,
        recon_hours: int,
        pending_command_hours: int
    ) -> HealthThreshold:
        """
        Update health thresholds. Creates new record and deactivates old ones.
        """
        await self.session.execute(
            update(HealthThreshold)
            .where(HealthThreshold.is_active == True)
            .values(is_active=False)
        )

        new_threshold = HealthThreshold(
            check_in_hours=check_in_hours,
            recon_hours=recon_hours,
            pending_command_hours=pending_command_hours,
            is_active=True
        )
        self.session.add(new_threshold)
        await self.session.flush()
        await self.session.refresh(new_threshold)
        
        return new_threshold

    async def get_compliance_group(self) -> str:
        """
        Get the compliance group name.
        """
        value = await self.get_setting("compliance_group")
        return value if value else "Compliance"

    async def set_compliance_group(self, group_name: str) -> None:
        """
        Set the compliance group name.
        """
        await self.set_setting("compliance_group", group_name)

    async def get_monitored_groups(self) -> List[str]:
        """
        Get the list of monitored groups.
        """
        value = await self.get_setting("monitored_groups")
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return []

    async def set_monitored_groups(self, groups: List[str]) -> None:
        """
        Set the list of monitored groups.
        """
        await self.set_setting("monitored_groups", json.dumps(groups))


class DeviceCacheRepository:
    """
    Repository for managing cached device health data.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cached_device(self, device_id: int) -> Optional[CachedDeviceHealth]:
        """
        Get cached device health data if not expired.
        """
        result = await self.session.execute(
            select(CachedDeviceHealth)
            .where(CachedDeviceHealth.device_id == device_id)
            .where(CachedDeviceHealth.expires_at > datetime.now(timezone.utc))
        )
        return result.scalar_one_or_none()

    async def get_all_cached_devices(self) -> List[CachedDeviceHealth]:
        """
        Get all cached device health data that hasn't expired.
        """
        result = await self.session.execute(
            select(CachedDeviceHealth)
            .where(CachedDeviceHealth.expires_at > datetime.now(timezone.utc))
            .order_by(CachedDeviceHealth.device_name)
        )
        return list(result.scalars().all())

    async def cache_device_health(
        self,
        device_health: DeviceHealth,
        ttl_seconds: int = 300
    ) -> CachedDeviceHealth:
        """
        Cache or update device health data.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        result = await self.session.execute(
            select(CachedDeviceHealth)
            .where(CachedDeviceHealth.device_id == device_health.device.id)
        )
        cached = result.scalar_one_or_none()

        if cached:
            cached.device_name = device_health.device.name
            cached.serial_number = device_health.device.serial_number
            cached.model = device_health.device.model
            cached.os_version = device_health.device.os_version
            cached.last_contact_time = device_health.device.last_contact_time
            cached.last_inventory_update = device_health.device.last_inventory_update
            cached.check_in_ok = device_health.health.check_in_ok
            cached.recon_ok = device_health.health.recon_ok
            cached.has_failed_policies = device_health.health.has_failed_policies
            cached.has_failed_mdm_commands = device_health.health.has_failed_mdm_commands
            cached.has_pending_mdm_commands = device_health.health.has_pending_mdm_commands
            cached.is_compliant = device_health.health.is_compliant
            cached.smart_group_memberships = device_health.health.smart_group_memberships
            cached.status = device_health.status.value
            cached.cached_at = datetime.now(timezone.utc)
            cached.expires_at = expires_at
        else:
            cached = CachedDeviceHealth(
                device_id=device_health.device.id,
                device_name=device_health.device.name,
                serial_number=device_health.device.serial_number,
                model=device_health.device.model,
                os_version=device_health.device.os_version,
                last_contact_time=device_health.device.last_contact_time,
                last_inventory_update=device_health.device.last_inventory_update,
                check_in_ok=device_health.health.check_in_ok,
                recon_ok=device_health.health.recon_ok,
                has_failed_policies=device_health.health.has_failed_policies,
                has_failed_mdm_commands=device_health.health.has_failed_mdm_commands,
                has_pending_mdm_commands=device_health.health.has_pending_mdm_commands,
                is_compliant=device_health.health.is_compliant,
                smart_group_memberships=device_health.health.smart_group_memberships,
                status=device_health.status.value,
                expires_at=expires_at
            )
            self.session.add(cached)

        await self.session.flush()
        return cached

    async def clear_expired_cache(self) -> int:
        """
        Remove expired cache entries. Returns number of deleted records.
        """
        result = await self.session.execute(
            select(CachedDeviceHealth)
            .where(CachedDeviceHealth.expires_at <= datetime.now(timezone.utc))
        )
        expired = list(result.scalars().all())
        
        for entry in expired:
            await self.session.delete(entry)
        
        await self.session.flush()
        return len(expired)


class UserRepository:
    """
    Repository for managing users.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        username: str,
        hashed_password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        is_superuser: bool = False
    ) -> User:
        """
        Create a new user.
        """
        user = User(
            username=username,
            hashed_password=hashed_password,
            email=email,
            full_name=full_name,
            is_superuser=is_superuser
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp.
        """
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.now(timezone.utc))
        )
        await self.session.flush()
