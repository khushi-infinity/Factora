"""Route modules.

One module per concern, mounted under `/api`. M1 ships `health` only; the product routes
(twin, predictions, explanations, parts, impact, work orders) arrive with their milestones and
must call `app/db/` and `app/ml/` — never build SQL or import the connector directly.
"""
