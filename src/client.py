import httpx
import asyncio
import time
import functools

from datetime import datetime, timezone
from collections.abc import Iterator
from typing import ParamSpec, TypeVar, Literal
from collections.abc import Callable, Awaitable

from config import ENDPOINTS
from models import Check, StatusCode, LatencyRule, ContentRule, Endpoint, Report


# Type vars to preserve the decorated function's signature through @retry. 
P = ParamSpec("P")
R = TypeVar("R")


def retry(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R | None]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        for tries in range(3):
            try:
                return await func(*args, **kwargs)
            
            except httpx.RequestError:
                await asyncio.sleep(2**tries)
        
        # the aggregator will treat a missing Check as "down"        
        return None
    return wrapper

    

@retry
async def fetch_one(client:httpx.AsyncClient, url:str) -> Check | None:
    """Measure a single endpoint and return its Check, or None if unreachable."""
    start = time.perf_counter()
    response = await client.get(url, timeout=5)
    # Measure round-trip time manually so it also covers retries later on.
    latency_ms = int((time.perf_counter() - start) * 1000)
    measurement = Check(latency= latency_ms, status_code= response.status_code, body= response.text)
    return measurement


    
async def fetch_all(endpoints: list[Endpoint]) -> list[tuple[Endpoint, Check | None]]:
    """ Measure all endpoints concurrently, sharing a single client. """
    async with httpx.AsyncClient() as client:
        coros = [fetch_one(client, ep.url) for ep in endpoints]
        results = await asyncio.gather(*coros)
        return list(zip(endpoints, results))


def build_reports(results: list[tuple[Endpoint, Check | None]]) -> list[Report]:
    """Turn raw measurements into per-endpoint health reports."""
    reports: list[Report] = []
    for endpoint, measurement in results:
        state: Literal["healthy", "degraded", "down"]
        # A missing measurement means the endpoint never answered: down, no rules to run.
        if measurement is None:
            state = "down"
        else:
            state = "healthy" # assume healthy; a failing rule downgrades it
            
            for rule in endpoint.rules:
                if not rule.check(measurement):
                    # Status/content failures are fatal; latency only degrades.
                    if isinstance(rule, (StatusCode, ContentRule)):
                        state = "down"
                        break
                    if isinstance(rule, LatencyRule):
                        state = "degraded"
                        
                        
        # # The front shows the latency budget, so pull it from the LatencyRule.
        threshold = None
        for rule in endpoint.rules:
            if isinstance(rule, LatencyRule):
                threshold = rule.threshold
                break

        reports.append(Report(name= endpoint.name,
                        url= endpoint.url,
                        state= state,
                        status_code= measurement.status_code if measurement is not None else 0,
                        latency_ms = measurement.latency if measurement is not None else 0,
                        threshold= threshold,
                        checked_at= datetime.now(timezone.utc).isoformat()
                        ))
               
    return reports
    

def monitor_stream() -> Iterator[list[Report]]:
    """Continuously measure all endpoints, yielding one fresh batch per cycle.
    Runs forever; the caller consumes each batch and stores it. Sleeping after
    the yield keeps memory flat: no batch is ever accumulated. """
    
    while True:
        results = asyncio.run(fetch_all(ENDPOINTS))
        reports = build_reports(results)
        yield reports 
        time.sleep(40)



