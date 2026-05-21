# python/src/server/core/app_state.py


class AppState:
    """Global application state shared across core modules."""

    initialization_complete: bool = False


app_state = AppState()
