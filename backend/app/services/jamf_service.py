import httpx
from typing import Optional
from datetime import datetime, timedelta, timezone
from app.core.config import get_settings
from app.models.device import JamfToken
from fastapi import HTTPException, status
import asyncio
from functools import lru_cache

settings = get_settings()


class JamfAPIService:
    def __init__(self):
        self.base_url = settings.jamf_url.rstrip('/')
        self.client_id = settings.jamf_client_id
        self.client_secret = settings.jamf_client_secret
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def _get_token(self) -> str:
        async with self._lock:
            if self._token and self._token_expiry:
                if datetime.now(timezone.utc) < self._token_expiry - timedelta(minutes=5):
                    return self._token
            
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
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Failed to authenticate with Jamf Pro"
                    )
                
                token_data = response.json()
                self._token = token_data["access_token"]
                self._token_expiry = datetime.now(timezone.utc) + timedelta(
                    seconds=token_data["expires_in"]
                )
                
                return self._token
    
    async def _make_request(self, method: str, endpoint: str, **kwargs):
        token = await self._get_token()
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await getattr(client, method.lower())(
                f"{self.base_url}{endpoint}",
                **kwargs
            )
            
            if response.status_code == 401:
                self._token = None
                self._token_expiry = None
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Jamf authentication failed"
                )
            
            return response
    
    async def get_all_computers(self) -> list[dict]:
        response = await self._make_request("GET", "/api/v1/computers-inventory")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve computers from Jamf Pro"
            )
        
        data = response.json()
        return data.get("results", [])
    
    async def get_computer_detail(self, computer_id: int) -> dict:
        response = await self._make_request(
            "GET", 
            f"/api/v1/computers-inventory-detail/{computer_id}"
        )
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Computer with ID {computer_id} not found"
            )
        elif response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve computer details"
            )
        
        return response.json()
    
    async def get_computer_management(self, computer_id: int) -> dict:
        response = await self._make_request(
            "GET",
            f"/api/v2/computers/{computer_id}/management-data"
        )
        
        if response.status_code != 200:
            return {}
        
        return response.json()
    
    async def get_failed_policies(self, computer_id: int) -> list[dict]:
        management_data = await self.get_computer_management(computer_id)
        failed_policies = []
        
        if "policies" in management_data:
            for policy in management_data.get("policies", []):
                if policy.get("failed", False):
                    failed_policies.append(policy)
        
        return failed_policies
    
    async def get_mdm_commands(self, computer_id: int) -> dict:
        response = await self._make_request(
            "GET",
            f"/api/v2/mdm/commands",
            params={"clientManagementId": computer_id}
        )
        
        if response.status_code != 200:
            return {"failed": [], "pending": []}
        
        commands = response.json().get("results", [])
        
        failed = [cmd for cmd in commands if cmd.get("status") == "Failed"]
        pending = [
            cmd for cmd in commands 
            if cmd.get("status") in ["Pending", "InProgress"]
        ]
        
        return {"failed": failed, "pending": pending}
    
    async def get_smart_groups(self) -> list[dict]:
        response = await self._make_request("GET", "/JSSResource/computergroups")
        
        if response.status_code != 200:
            return []
        
        groups = response.json().get("computer_groups", [])
        return [g for g in groups if g.get("is_smart", False)]
    
    async def get_computer_group_membership(self, computer_id: int) -> list[str]:
        response = await self._make_request(
            "GET",
            f"/JSSResource/computers/id/{computer_id}"
        )
        
        if response.status_code != 200:
            return []
        
        computer = response.json().get("computer", {})
        groups = computer.get("groups_accounts", {}).get("computer_group_memberships", [])
        
        return [g.get("name") for g in groups if g.get("name")]


@lru_cache()
def get_jamf_service() -> JamfAPIService:
    return JamfAPIService()
