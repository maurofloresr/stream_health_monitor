from __future__ import annotations
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
from typing import Literal

@dataclass
class Endpoint:
        name: str
        url: str
        rules: list[HealthRule]


class HealthRule(ABC):
    @abstractmethod
    def check(self, response:Check) -> bool:
        ...


@dataclass
class Check:
    latency: int
    status_code: int
    body: str


class LatencyRule(HealthRule):
    def __init__(self,threshold: int):
        self.threshold = threshold
        
    def check(self, response:Check) -> bool:
        return response.latency <= self.threshold


class StatusCode(HealthRule):
    def __init__(self, codes:set[int]):
        self.codes = codes
        
    def check(self, response:Check) -> bool:
        return response.status_code in self.codes
    
class ContentRule(HealthRule):
    def __init__(self, expected: str | None = None) -> None:
        self.expected = expected

    def check(self, response: Check) -> bool:
        # Valid content = parseable JSON, plus the expected marker if one was set.
        try:
            json.loads(response.body)
        except json.JSONDecodeError:
            return False
        if self.expected is not None and self.expected not in response.body:
            return False
        return True
    

@dataclass
class Report:
    name:str
    url:str
    state: Literal["healthy","degraded","down"]
    status_code: int
    latency_ms: int
    threshold: int | None
    checked_at: str
    