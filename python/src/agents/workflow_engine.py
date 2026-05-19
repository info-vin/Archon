# Phase 5.1.8 / L2 Modularization
# This file is now a Facade to ensure 100% backward compatibility.
# The actual implementation has been split into the `workflow/` package.
from .workflow import WorkflowEngine

__all__ = ["WorkflowEngine"]
