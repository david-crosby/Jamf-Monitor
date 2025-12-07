from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.models.device import (
    DeviceHealth, DeviceListResponse, HealthThresholds, HealthStatus
)
from app.services.health_service import get_health_service, HealthCheckService
from app.core.security import verify_token

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=DeviceListResponse)
async def get_all_devices(
    status_filter: Optional[HealthStatus] = Query(None),
    health_service: HealthCheckService = Depends(get_health_service),
    _: dict = Depends(verify_token)
):
    devices = await health_service.check_all_devices()
    
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
    health_service: HealthCheckService = Depends(get_health_service),
    _: dict = Depends(verify_token)
):
    return await health_service.check_device_health(device_id)


@router.get("/status/summary")
async def get_status_summary(
    health_service: HealthCheckService = Depends(get_health_service),
    _: dict = Depends(verify_token)
):
    devices = await health_service.check_all_devices()
    
    healthy = sum(1 for d in devices if d.status == HealthStatus.HEALTHY)
    caution = sum(1 for d in devices if d.status == HealthStatus.CAUTION)
    unhealthy = sum(1 for d in devices if d.status == HealthStatus.UNHEALTHY)
    
    return {
        "total": len(devices),
        "healthy": healthy,
        "caution": caution,
        "unhealthy": unhealthy,
        "percentages": {
            "healthy": round((healthy / len(devices) * 100) if devices else 0, 1),
            "caution": round((caution / len(devices) * 100) if devices else 0, 1),
            "unhealthy": round((unhealthy / len(devices) * 100) if devices else 0, 1)
        }
    }
