import os
from typing import Literal, Optional, TypedDict

import aiohttp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DevinAPIAuthResponse(TypedDict):
    status: str
    org_id: str


class DevinAPISessionResponse(TypedDict):
    session_id: str
    url: str
    is_new_session: Optional[bool]


class DevinAPISessionStatusResponse(TypedDict):
    session_id: str
    status: str
    title: str
    created_at: str
    updated_at: str
    snapshot_id: Optional[str]
    playbook_id: Optional[str]
    structured_output: dict
    status_enum: (
        Literal[
            "working",
            "blocked",
            "finished",
            "suspend_requested",
            "resume_requested",
            "resumed",
        ]
        | None
    )


class DevinAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.base_url = "https://api.devin.ai/v1"

    async def check_auth(self) -> DevinAPIAuthResponse:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/auth_status",
                headers=self.headers,
            ) as response:
                return await response.json()

    async def start_session(self, prompt: str) -> DevinAPISessionResponse:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/sessions",
                headers=self.headers,
                json={"prompt": prompt},
            ) as response:
                response_data = await response.json()
                return response_data

    async def get_session_status(
        self, session_id: str
    ) -> DevinAPISessionStatusResponse | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/session/{session_id}",
                headers=self.headers,
            ) as response:
                response_data = await response.json()
                if (
                    "detail" in response_data
                    and response_data["detail"] == "Session not found"
                ):
                    return None
                return response_data


async def main():
    api_key = os.getenv("DEVIN_API_KEY")
    if not api_key:
        raise ValueError("DEVIN_API_KEY environment variable is required")
    client = DevinAPIClient(api_key)
    auth_status = await client.check_auth()
    print("AUTH STATUS: ", auth_status)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
