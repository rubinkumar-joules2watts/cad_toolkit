from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.macros.service import execute_macro, list_macro_definitions


router = APIRouter(prefix="/macros", tags=["macros"])


class MacroExecuteRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("")
def list_macros() -> dict[str, Any]:
    return list_macro_definitions()


@router.post("/{macro_id}/execute")
def run_macro(macro_id: str, request: MacroExecuteRequest) -> dict[str, Any]:
    return execute_macro(macro_id, request.params)
