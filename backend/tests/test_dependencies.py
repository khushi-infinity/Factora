"""Toolchain smoke test.

PROJECT_SPEC.md §4 lists the approved stack; this test fails loudly if any of it cannot actually be
imported on the interpreter the project runs on — which is exactly the kind of breakage that would
otherwise surface mid-demo.
"""

from __future__ import annotations

import importlib

import pytest

EXPECTED_IMPORTS = (
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic_settings",
    "snowflake.connector",
    "pandas",
    "sklearn",
    "joblib",
    "pytest",
    "httpx",
)


@pytest.mark.parametrize("module_name", EXPECTED_IMPORTS)
def test_declared_dependency_imports(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None


def test_ml_stack_is_usable_not_just_importable() -> None:
    """A tiny real computation, so a broken native build shows up here rather than in M3."""
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression

    frame = pd.DataFrame({"day": np.arange(10, dtype=float)})
    frame["vibration_rms"] = 40.0 + frame["day"] * 1.5

    model = LinearRegression().fit(frame[["day"]], frame["vibration_rms"])

    assert round(float(model.coef_[0]), 3) == 1.5
    assert model.predict(pd.DataFrame({"day": [20.0]}))[0] > frame["vibration_rms"].max()
    assert callable(joblib.dump)
