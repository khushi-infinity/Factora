"""Local feature work and model artefacts.

Intentionally empty at M1. From M3 this package holds pandas / scikit-learn / joblib code for
feature engineering experiments and model training, with two rules carried over from the spec
(PROJECT_SPEC.md §5 and §7):

  * anything that produces the twin's health score, prediction or cost must either run in
    Snowflake or be persisted back with a `model_version` and `computed_at` — a score that exists
    only inside this process is not allowed to reach the UI;
  * trained artefacts are loaded via joblib from a path in configuration, and those files are
    build output: never committed (see .gitignore).
"""
