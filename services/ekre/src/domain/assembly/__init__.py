"""Context assembly and response packaging (handbook Chapters 26-27)."""

from domain.assembly.citations import to_candidate
from domain.assembly.engine import ContextAssemblyEngine
from domain.assembly.errors import AssemblyError, AssemblyErrorType
from domain.assembly.models import AssemblyResult, ContextMetrics
from domain.assembly.policy import AssemblyPolicy, AssemblySettingsLike
from domain.assembly.selection import (
    ContextSelector,
    SelectedContext,
    SelectionResult,
)
from domain.assembly.tokens import estimate_tokens, optimize_content

__all__ = [
    "AssemblyError",
    "AssemblyErrorType",
    "AssemblyPolicy",
    "AssemblyResult",
    "AssemblySettingsLike",
    "ContextAssemblyEngine",
    "ContextMetrics",
    "ContextSelector",
    "SelectedContext",
    "SelectionResult",
    "estimate_tokens",
    "optimize_content",
    "to_candidate",
]
