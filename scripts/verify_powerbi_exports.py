"""Validate versioned Power BI inputs on any clone, without raw data."""

from __future__ import annotations

import json
import sys

from mediscope.visualization.exports import ExportError, verify_exports

try:
    print(json.dumps(verify_exports(), indent=2))
except ExportError as error:
    print(json.dumps({"status": "FAIL", "error": str(error)}, indent=2))
    sys.exit(2)
