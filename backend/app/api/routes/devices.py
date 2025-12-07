from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import (
    DeviceHealth, DeviceListResponse, HealthStatus
)
from app.services.health_service import HealthCheckService
from app.core.security import verify_token
from app.core.database import get_db
from app.services.jamf_service import get_jamf_service, JamfAPIService

router = APIRouter(prefix="/devices", tags=["devices"])


async def get_health_service_with_db(
    db: AsyncSession = Depends(get_db),
    jamf_service: JamfAPIService = Depends(get_jamf_service)
) -> HealthCheckService:
    """
    Dependency injection for HealthCheckService with database session.
    """
    return HealthCheckService(jamf_service, db)


@router.get("/", response_model=DeviceListResponse)
async def get_all_devices(
    status_filter: Optional[HealthStatus] = Query(None),
    use_cache: bool = Query(True, description="Use cached data if available"),
    health_service: HealthCheckService = Depends(get_health_service_with_db),
    _: dict = Depends(verify_token)
):
    """
    Get all devices with optional status filtering and caching.
    """
    devices = await health_service.check_all_devices(use_cache=use_cache)
    
    if status_filter:
        devices = [d for d in devices if d.status == status_filter]
    
    healthy = sum(1 for d in devices if d.status == HealthStatus.HEALTHY)
    caution = sum(1 for d in devices if d.status == HealthStatus.CAUTION)
    unhealthy = sum(1 for d in devices if d.status == HealthStatus.UNHEALTHY)
    
    return DeviceListResponse(
        total=len(devices),
        devices=devices,
        healthy_count=healthy,
        caution_count=caution,
        unhealthy_count=unhealthy
    )


@router.get("/{device_id}", response_model=DeviceHealth)
async def get_device_health(
    device_id: int,
    use_cache: bool = Query(True, description="Use cached data if available"),
    health_service: HealthCheckService = Depends(get_health_service_with_db),
    _: dict = Depends(verify_token)
):
    """
    Get health status for a specific device.
    """
    return await health_service.check_device_health(device_id, use_cache=use_cache)


@router.get("/status/summary")
async def get_status_summary(
    use_cache: bool = Query(True, description="Use cached data if available"),
    health_service: HealthCheckService = Depends(get_health_service_with_db),
    _: dict = Depends(verify_token)
):
    """
    Get summary statistics of device health status.
    """
    devices = await health_service.check_all_devices(use_cache=use_cache)
    
    healthy = sum(1 for d in devices if d.status == HealthStatus.HEALTHY)
    caution = sum(1 for d in devices if d.status == HealthStatus.CAUTION)
    unhealthy = sum(1 for d in devices if d.status == HealthStatus.UNHEALTHY)
    
    total = len(devices)
    
    return {
        "total": total,
        "healthy": healthy,
        "caution": caution,
        "unhealthy": unhealthy,
        "percentages": {
            "healthy": round((healthy / total * 100) if total else 0, 1),
            "caution": round((caution / total * 100) if total else 0, 1),
            "unhealthy": round((unhealthy / total * 100) if total else 0, 1)
        }
    }
