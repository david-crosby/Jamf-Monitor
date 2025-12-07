import httpx
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from app.core.config import get_settings
from app.models.device import JamfToken
from fastapi import HTTPException, status
import asyncio
from functools import lru_cache

settings = get_settings()
logger = logging.getLogger(__name__)


class JamfAPIService:
    """
    Service for interacting with Jamf Pro API.
    Handles authentication, token management, and API requests.
    """
    
    def __init__(self):
        self.base_url = settings.jamf_url.rstrip('/')
        self.client_id = settings.jamf_client_id
        self.client_secret = settings.jamf_client_secret
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def _get_token(self) -> str:
        """
        Get or refresh OAuth token for Jamf Pro API.
        Thread-safe with automatic token refresh.
        """
        async with self._lock:
            if self._token and self._token_expiry:
                if datetime.now(timezone.utc) < self._token_expiry - timedelta(minutes=5):
                    return self._token
            
            logger.info("Requesting new Jamf Pro API token")
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/api/oauth/token",
                        data={
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                            "grant_type": "client_credentials"
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to authenticate with Jamf Pro: {response.status_code}")
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Failed to authenticate with Jamf Pro"
                        )
                    
                    token_data = response.json()
                    self._token = token_data["access_token"]
                    self._token_expiry = datetime.now(timezone.utc) + timedelta(
                        seconds=token_data["expires_in"]
                    )
                    
                    logger.info("Successfully obtained Jamf Pro API token")
                    return self._token
                    
            except httpx.RequestError as e:
                logger.error(f"Network error connecting to Jamf Pro: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to connect to Jamf Pro"
                )
    
    async def _make_request(self, method: str, endpoint: str, **kwargs):
        """
        Make authenticated request to Jamf Pro API with error handling.
        """
        token = await self._get_token()
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await getattr(client, method.lower())(
                    f"{self.base_url}{endpoint}",
                    **kwargs
                )
                
                if response.status_code == 401:
                    logger.warning("Jamf API token expired, refreshing")
                    self._token = None
                    self._token_expiry = None
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Jamf authentication failed"
                    )
                
                return response
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling Jamf API: {endpoint}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Jamf Pro request timed out"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error calling Jamf API {endpoint}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error communicating with Jamf Pro"
            )
    
    async def get_all_computers(self) -> list[dict]:
        """
        Retrieve all computers from Jamf Pro inventory.
        """
        logger.debug("Fetching all computers from Jamf Pro")
        response = await self._make_request("GET", "/api/v1/computers-inventory")
        
        if response.status_code != 200:
            logger.error(f"Failed to retrieve computers: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve computers from Jamf Pro"
            )
        
        data = response.json()
        computers = data.get("results", [])
        logger.info(f"Retrieved {len(computers)} computers from Jamf Pro")
        return computers
    
    async def get_computer_detail(self, computer_id: int) -> dict:
        """
        Get detailed information for a specific computer.
        """
        logger.debug(f"Fetching details for computer ID {computer_id}")
        response = await self._make_request(
            "GET", 
            f"/api/v1/computers-inventory-detail/{computer_id}"
        )
        
        if response.status_code == 404:
            logger.warning(f"Computer with ID {computer_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Computer with ID {computer_id} not found"
            )
        elif response.status_code != 200:
            logger.error(f"Failed to retrieve computer {computer_id}: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve computer details"
            )
        
        return response.json()
    
    async def get_computer_management(self, computer_id: int) -> dict:
        """
        Get management data for a specific computer.
        """
        logger.debug(f"Fetching management data for computer ID {computer_id}")
        response = await self._make_request(
            "GET",
            f"/api/v2/computers/{computer_id}/management-data"
        )
        
        if response.status_code != 200:
            logger.warning(f"No management data for computer {computer_id}")
            return {}
        
        return response.json()
    
    async def get_failed_policies(self, computer_id: int) -> list[dict]:
        """
        Get failed policies for a specific computer.
        """
        management_data = await self.get_computer_management(computer_id)
        failed_policies = []
        
        if "policies" in management_data:
            for policy in management_data.get("policies", []):
                if policy.get("failed", False):
                    failed_policies.append(policy)
        
        logger.debug(f"Computer {computer_id} has {len(failed_policies)} failed policies")
        return failed_policies
    
    async def get_mdm_commands(self, computer_id: int) -> dict:
        """
        Get MDM commands for a specific computer.
        """
        logger.debug(f"Fetching MDM commands for computer ID {computer_id}")
        response = await self._make_request(
            "GET",
            f"/api/v2/mdm/commands",
            params={"clientManagementId": computer_id}
        )
        
        if response.status_code != 200:
            logger.warning(f"No MDM commands for computer {computer_id}")
            return {"failed": [], "pending": []}
        
        commands = response.json().get("results", [])
        
        failed = [cmd for cmd in commands if cmd.get("status") == "Failed"]
        pending = [
            cmd for cmd in commands 
            if cmd.get("status") in ["Pending", "InProgress"]
        ]
        
        logger.debug(f"Computer {computer_id}: {len(failed)} failed, {len(pending)} pending MDM commands")
        return {"failed": failed, "pending": pending}
    
    async def get_smart_groups(self) -> list[dict]:
        """
        Get all smart computer groups.
        """
        logger.debug("Fetching smart groups from Jamf Pro")
        response = await self._make_request("GET", "/JSSResource/computergroups")
        
        if response.status_code != 200:
            logger.warning("Failed to retrieve smart groups")
            return []
        
        groups = response.json().get("computer_groups", [])
        smart_groups = [g for g in groups if g.get("is_smart", False)]
        logger.info(f"Retrieved {len(smart_groups)} smart groups")
        return smart_groups
    
    async def get_computer_group_membership(self, computer_id: int) -> list[str]:
        """
        Get group memberships for a specific computer.
        """
        logger.debug(f"Fetching group memberships for computer ID {computer_id}")
        response = await self._make_request(
            "GET",
            f"/JSSResource/computers/id/{computer_id}"
        )
        
        if response.status_code != 200:
            logger.warning(f"Failed to retrieve group memberships for computer {computer_id}")
            return []
        
        computer = response.json().get("computer", {})
        groups = computer.get("groups_accounts", {}).get("computer_group_memberships", [])
        
        group_names = [g.get("name") for g in groups if g.get("name")]
        logger.debug(f"Computer {computer_id} is member of {len(group_names)} groups")
        return group_names


@lru_cache()
def get_jamf_service() -> JamfAPIService:
    """
    Dependency injection for JamfAPIService.
    """
    return JamfAPIService()
