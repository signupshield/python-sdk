from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal, Optional


@dataclass(frozen=True)
class ScoreParams:
    email: str
    ip: Optional[str] = None


@dataclass(frozen=True)
class ScoreResult:
    score: int
    risk: Literal["low", "medium", "high"]
    disposable: bool
    free_provider: bool
    mx_valid: bool
    ip_reputation: Literal["residential", "datacenter", "proxy", "tor"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScoreResult":
        return cls(
            score=data["score"],
            risk=data["risk"],
            disposable=data["disposable"],
            free_provider=data["free_provider"],
            mx_valid=data["mx_valid"],
            ip_reputation=data["ip_reputation"],
        )


@dataclass(frozen=True)
class BatchParams:
    items: list[ScoreParams]


@dataclass(frozen=True)
class BatchResult:
    results: list[ScoreResult]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BatchResult":
        return cls(results=[ScoreResult.from_dict(r) for r in data["results"]])
