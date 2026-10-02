"""Factora FastAPI backend (BFF).

Layout and boundaries (PROJECT_SPEC.md §3.5):
    app/api/   route modules — health now; twin, predictions, parts, work orders later
    app/db/    the ONLY package allowed to import the Snowflake connector
    app/ml/    pandas / scikit-learn / joblib feature work and model artefacts (M3+)

The SPA never queries Snowflake and this package never renders UI.
"""

__version__ = "0.1.0"
