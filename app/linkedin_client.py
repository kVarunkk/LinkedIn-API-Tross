"""LinkedIn Voyager API client."""
import httpx
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LinkedInClient:
    """Makes authenticated requests to LinkedIn's internal Voyager REST API."""

    BASE_URL = "https://www.linkedin.com"

    def __init__(
        self,
        li_at: str,
        jsessionid: str,
        user_agent: Optional[str] = None,
        li_track: Optional[str] = None,
    ):
        self.li_at = li_at
        self.jsessionid = jsessionid
        self.session = httpx.AsyncClient(timeout=30.0)
        self._csrf_token = jsessionid  # constant works with valid session

        default_ua = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        default_track = {
            "clientVersion": "0.2.7003",
            "mpVersion": "0.2.7003",
            "osName": "web",
            "timezoneOffset": 5.5,
            "timezone": "Asia/Calcutta",
            "deviceFormFactor": "DESKTOP",
            "mpName": "web",
            "displayDensity": 1,
            "displayWidth": 1920,
            "displayHeight": 1080,
        }
        track_json = li_track if li_track else json.dumps(default_track)

        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "csrf-token": self._csrf_token,
            "x-li-lang": "en_US",
            "x-restli-protocol-version": "2.0.0",
            "x-li-track": track_json,
            "referer": "https://www.linkedin.com/feed/",
            "origin": "https://www.linkedin.com",
            "user-agent": user_agent or default_ua,
            "cookie": f'li_at={li_at}; JSESSIONID="{jsessionid}";',
        }
        logger.info("LinkedInClient created")

    async def get_full_profile(self, vanity_name: str) -> Dict[str, Any]:
        url = (
            f"{self.BASE_URL}/voyager/api/identity/dash/profiles"
            f"?q=memberIdentity"
            f"&memberIdentity={vanity_name}"
            f"&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-96"
        )
        logger.info(f"[GET] {url}")
        try:
            response = await self.session.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            logger.info("Profile data received successfully")
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"LinkedIn returned {e.response.status_code}: {e.response.text[:300]}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    async def close(self):
        await self.session.aclose()
        logger.info("LinkedInClient closed")