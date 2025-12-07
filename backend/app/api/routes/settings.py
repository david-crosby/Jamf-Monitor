from fastapi import APIRouter, Depends
from app.models.device import HealthThresholds
from app.services.health_service import get_health_service, HealthCheckService
from app.core.security import verify_token

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/thresholds", response_model=HealthThresholds)
async def get_thresholds(
    health_service: HealthCheckService = Depends(get_health_service),
    _: dict = Depends(verify_token)
):
    return health_service.get_thresholds()


@router.put("/thresholds", response_model=HealthThresholds)
async def update_thresholds(
    thresholds: HealthThresholds,
    health_service: HealthCheckService = Depends(get_health_service),
    _: dict = Depends(verify_token)
):
    health_service.set_thresholds(
        check_in_hours=thresholds.check_in_hours,
        recon_hours=thresholds.recon_hours,
        pending_command_hours=thresholds.pending_command_hours
    )
    
    return health_service.get_thresholds()


@router.get("/monitored-groups")
async def get_monitored_groups(
    health_service: HealthCheckService = Depends(get_health_service),
    _: dict = Depends(verify_token)
):
    return {
        "compliance_group": health_service.compliance_group_name,
        "monitored_groups": health_service.monitored_groups
    }


@router.put("/monitored-groups")
async def update_monitored_groups(
    groups: dict,
    health_service: HealthCheckService = Depends(get_health_service),
    _: dict = Depends(verify_token)
):
    if "compliance_group" in groups:
        health_service.compliance_group_name = groups["compliance_group"]
    
    if "monitored_groups" in groups:
        health_service.monitored_groups = groups["monitored_groups"]
    
    return {
        "compliance_group": health_service.compliance_group_name,
        "monitored_groups": health_service.monitored_groups
    }
