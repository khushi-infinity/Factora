"""Snowflake access layer.

This package is the **only** place in the codebase allowed to import the Snowflake connector
(PROJECT_SPEC.md §3.5). Route modules call functions from here; they never build connections or
SQL themselves, and no credential ever travels further than this package.
"""

from .snowflake import ProbeResult, probe_snowflake, reset_probe_cache

__all__ = ["ProbeResult", "probe_snowflake", "reset_probe_cache"]
