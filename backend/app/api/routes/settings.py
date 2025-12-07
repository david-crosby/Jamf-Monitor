from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import HealthThresholds
from app.services.health_service import HealthCheckService
from app.core.security import verify_token
from app.core.database import get_db
from app.services.jamf_service import get_jamf_service, JamfAPIService

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_health_service_with_db(
    db: AsyncSession = Depends(get_db),
    jamf_service: JamfAPIService = Depends(get_jamf_service)
) -> HealthCheckService:
    """
    Dependency injection for HealthCheckService with database session.
    """
    return HealthCheckService(jamf_service, db)


@router.get("/thresholds", response_model=HealthThresholds)
async def get_thresholds(
    health_service: HealthCheckService = Depends(get_health_service_with_db),
    _: dict = Depends(verify_token)
):
    """
    Get current health check thresholds.
    """
    return await health_service.get_thresholds()


@router.put("/thresholds", response_model=HealthThresholds)
async def update_thresholds(
    thresholds: HealthThresholds,
    health_service: HealthCheckService = Depends(get_health_service_with_db),
    _: dict = Depends(verify_token)
):
    """
    Update health check thresholds.
    """
    await health_service.set_thresholds(
        check_in_hours=thresholds.check_in_hours,
        recon_hours=thresholds.recon_hours,
        pending_command_hours=thresholds.pending_command_hours
    )
    
    return await health_service.get_thresholds()


@router.get("/monitored-groups")
async def get_monitored_groups(
    health_service: HealthCheckService = Depends(get_health_service_with_db),
    _: dict = Depends(verify_token)
):
    """
    Get compliance group and monitored groups configuration.
    """
    compliance_group = await health_service.get_compliance_group_name()
    monitored_groups = await health_service.get_monitored_groups()
    
    return {
        "compliance_group": compliance_group,
        "monitored_groups": monitored_groups
    }


@router.put("/monitored-groups")
async def update_monitored_groups(
    groups: dict,
    health_service: HealthCheckService = Depends(get_health_service_with_db),
    _: dict = Depends(verify_token)
):
    """
    Update compliance group and monitored groups configuration.
    """
    if "compliance_group" in groups:
        await health_service.set_compliance_group_name(groups["compliance_group"])
    
    if "monitored_groups" in groups:
        await health_service.set_monitored_groups(groups["monitored_groups"])
    
    compliance_group = await health_service.get_compliance_group_name()
    monitored_groups = await health_service.get_monitored_groups()
    
    return {
        "compliance_group": compliance_group,
        "monitored_groups": monitored_groups
    }
