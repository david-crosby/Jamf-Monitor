from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class ApplicationSettings(Base):
    """
    Stores application configuration that persists across restarts.
    """
    __tablename__ = "application_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(255), unique=True, nullable=False, index=True)
    setting_value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ApplicationSettings(key={self.setting_key}, value={self.setting_value})>"


class HealthThreshold(Base):
    """
    Stores health check threshold configurations.
    """
    __tablename__ = "health_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    check_in_hours = Column(Integer, nullable=False, default=24)
    recon_hours = Column(Integer, nullable=False, default=24)
    pending_command_hours = Column(Integer, nullable=False, default=6)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<HealthThreshold(check_in={self.check_in_hours}, "
            f"recon={self.recon_hours}, pending={self.pending_command_hours})>"
        )


class CachedDeviceHealth(Base):
    """
    Caches device health data to reduce Jamf API calls.
    """
    __tablename__ = "cached_device_health"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, unique=True, nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    serial_number = Column(String(255), nullable=False, index=True)
    model = Column(String(255))
    os_version = Column(String(100))
    
    last_contact_time = Column(DateTime(timezone=True))
    last_inventory_update = Column(DateTime(timezone=True))
    
    check_in_ok = Column(Boolean, nullable=False)
    recon_ok = Column(Boolean, nullable=False)
    has_failed_policies = Column(Boolean, nullable=False)
    has_failed_mdm_commands = Column(Boolean, nullable=False)
    has_pending_mdm_commands = Column(Boolean, nullable=False)
    is_compliant = Column(Boolean, nullable=False)
    
    smart_group_memberships = Column(JSON)
    status = Column(String(50), nullable=False, index=True)
    
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<CachedDeviceHealth(device_id={self.device_id}, name={self.device_name}, status={self.status})>"


class User(Base):
    """
    User authentication table for future multi-user support.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(username={self.username}, active={self.is_active})>"
