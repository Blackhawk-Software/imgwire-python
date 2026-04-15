from __future__ import annotations

from typing import Optional

from generated.imgwire_generated.api_client import ApiClient
from generated.imgwire_generated.configuration import Configuration

from imgwire.client.options import ImgwireClientOptions
from imgwire.resources import (
    CorsOriginsResource,
    CustomDomainResource,
    ImagesResource,
    MetricsResource,
)


class ImgwireClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.imgwire.dev",
        environment_id: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        backoff_factor: float = 0.5,
    ) -> None:
        self.options = ImgwireClientOptions(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            environment_id=environment_id,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

        configuration = Configuration(
            host=self.options.base_url, retries=self.options.max_retries
        )
        api_client = ApiClient(configuration=configuration)
        api_client.default_headers["Authorization"] = f"Bearer {self.options.api_key}"
        api_client.default_headers["User-Agent"] = "imgwire-python/0.1.0"
        if self.options.environment_id:
            api_client.default_headers["X-Environment-Id"] = self.options.environment_id

        self.api_client = api_client
        self.images = ImagesResource(api_client, self.options)
        self.custom_domain = CustomDomainResource(api_client)
        self.cors_origins = CorsOriginsResource(api_client)
        self.metrics = MetricsResource(api_client)
