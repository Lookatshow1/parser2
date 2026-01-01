from __future__ import annotations

import logging
import time

import httpx


class VkApiError(RuntimeError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"VK API error {code}: {message}")
        self.code = code
        self.message = message


class VkAdsClient:
    def __init__(self, access_token: str, version: str, base_url: str = "https://api.vk.com/method") -> None:
        self._access_token = access_token
        self._version = version
        self._base_url = base_url
        self._logger = logging.getLogger(__name__)

    def call(self, method_name: str, params: dict | None = None) -> dict:
        params = params or {}
        payload = {
            **params,
            "access_token": self._access_token,
            "v": self._version,
        }
        backoff = 1.0
        max_retries = 5
        with httpx.Client(timeout=10) as client:
            for _ in range(max_retries):
                response = client.post(f"{self._base_url}/{method_name}", data=payload)
                if response.status_code >= 500:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                data = response.json()
                if "error" in data:
                    error = data["error"]
                    code = int(error.get("error_code", 0))
                    message = error.get("error_msg", "Unknown error")
                    self._logger.warning("VK API error code=%s message=%s", code, message)
                    if code in {6, 9, 10, 29, 100}:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    raise VkApiError(code, message)
                return data
        raise RuntimeError("VK API request failed after retries")

    def get_statistics(
        self,
        account_id: int,
        ids: list[int],
        ids_type: str,
        date_from: str,
        date_to: str,
        period: str = "day",
    ) -> dict:
        return self.call(
            "ads.getStatistics",
            {
                "account_id": account_id,
                "ids": ",".join(str(value) for value in ids),
                "ids_type": ids_type,
                "date_from": date_from,
                "date_to": date_to,
                "period": period,
            },
        )
