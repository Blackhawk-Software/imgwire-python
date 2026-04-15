from __future__ import annotations

from datetime import datetime
from typing import Optional

from generated.imgwire_generated.api.metrics_api import MetricsApi
from generated.imgwire_generated.models.metrics_dataset_interval import (
    MetricsDatasetInterval,
)
from generated.imgwire_generated.models.metrics_datasets_schema import (
    MetricsDatasetsSchema,
)
from generated.imgwire_generated.models.metrics_stats_schema import MetricsStatsSchema

from imgwire.resources.base import BaseResource


class MetricsResource(BaseResource):
    def __init__(self, api_client) -> None:
        super().__init__(api_client)
        self._api = MetricsApi(api_client)

    def get_datasets(
        self,
        *,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
        interval: Optional[MetricsDatasetInterval | str] = None,
        tz: Optional[str] = None,
    ) -> MetricsDatasetsSchema:
        return self._call(
            lambda: self._api.metrics_get_datasets(
                date_start=date_start, date_end=date_end, interval=interval, tz=tz
            )
        )

    def get_stats(
        self,
        *,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
        interval: Optional[MetricsDatasetInterval | str] = None,
        tz: Optional[str] = None,
    ) -> MetricsStatsSchema:
        return self._call(
            lambda: self._api.metrics_get_stats(
                date_start=date_start, date_end=date_end, interval=interval, tz=tz
            )
        )
