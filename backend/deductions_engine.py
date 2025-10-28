import os
from datetime import date

# Calibration via env and auto-off after 2025-10-31
CALIBRATION_OCTOBER = os.environ.get("CALIBRATION_OCTOBER", "true").lower() == "true"
CALIB_FROM = date(2025, 9, 29)
CALIB_TO = date(2025, 10, 31)
NO_DATA_NO_DEDUCTION = os.environ.get("NO_DATA_NO_DEDUCTION", "true").lower() == "true"