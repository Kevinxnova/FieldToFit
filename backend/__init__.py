"""FieldToFit application version and legacy deployment configuration bridge."""
import os

__version__ = "1.1.0"

# Older deployments keep working while new documentation uses FIELDTOFIT_*.
for _key, _value in list(os.environ.items()):
    if _key.startswith("METIS_"):
        os.environ.setdefault("FIELDTOFIT_" + _key[6:], _value)
