"""
Open WebUI Pipe Function — Hermes identity-aware proxy.

Install this as a Function in Open WebUI (Admin → Functions → +).
Set it as the model for any chat that should route to Hermes.

What it does:
  1. Reads the logged-in user's email from Open WebUI's __user__ context
     (populated from the Google SSO session via oauth2-proxy).
  2. Forwards the full chat-completions request to Hermes with the
     X-Hermes-User-Email header added.
  3. Hermes reads that header, looks up users.json, and resolves the full
     user identity (Telegram ID, OAuth vault, Honcho memory scope, system-
     prompt profile) — nothing is exposed to the LLM.

Configuration (Valves — set in Open WebUI Function settings):
  hermes_url   Base URL of the Hermes API server, e.g. http://hermes:8642
  hermes_key   Value of API_SERVER_KEY in the Hermes container env.
"""

import json
from typing import AsyncGenerator, Iterator, Union

import httpx
from pydantic import BaseModel


class Pipe:
    class Valves(BaseModel):
        hermes_url: str = "http://hermes:8642"
        hermes_key: str = ""

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self):
        return [{"id": "hermes", "name": "Hermes"}]

    async def pipe(
        self,
        body: dict,
        __user__: dict | None = None,
    ) -> Union[str, AsyncGenerator, Iterator]:
        user_email = (__user__ or {}).get("email", "")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.valves.hermes_key}",
        }
        if user_email:
            headers["X-Hermes-User-Email"] = user_email

        url = f"{self.valves.hermes_url.rstrip('/')}/v1/chat/completions"
        stream = body.get("stream", False)

        async with httpx.AsyncClient(timeout=300) as client:
            if stream:
                async with client.stream("POST", url, json=body, headers=headers) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            payload = line[6:]
                            if payload.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(payload)
                                delta = (
                                    chunk.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if delta:
                                    yield delta
                            except (json.JSONDecodeError, IndexError, KeyError):
                                pass
            else:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                yield (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
