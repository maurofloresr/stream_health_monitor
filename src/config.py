from __future__ import annotations

from models import Endpoint, LatencyRule, StatusCode, ContentRule

# Latency thresholds are in milliseconds.
ENDPOINTS: list[Endpoint] = [
    # healthy: fast, stable, returns JSON
    Endpoint(
        name="GitHub API",
        url="https://api.github.com",
        rules=[LatencyRule(800), StatusCode({200}), ContentRule()],
    ),
    # healthy: weather API, returns JSON
    Endpoint(
        name="Open-Meteo",
        url="https://api.open-meteo.com/v1/forecast?latitude=-34.61&longitude=-58.38&current=temperature_2m",
        rules=[LatencyRule(1500), StatusCode({200}), ContentRule()],
    ),
    # degraded on purpose: threshold set very low so latency always fails
    Endpoint(
        name="JSONPlaceholder",
        url="https://jsonplaceholder.typicode.com/todos/1",
        rules=[LatencyRule(1), StatusCode({200}), ContentRule()],
    ),
    # down on purpose: this path returns 404, not in the allowed set
    Endpoint(
        name="Broken endpoint",
        url="https://jsonplaceholder.typicode.com/this-does-not-exist",
        rules=[LatencyRule(1500), StatusCode({200})],
    ),
]