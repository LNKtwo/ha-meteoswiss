"""BAFU Hydrological Data client.

TODO: No public REST API available for hydrodaten.admin.ch.

APIs tested and results:
  - https://www.hydrodaten.admin.ch/api/v1/stations → 302 redirect to HTML page
  - https://www.hydrodaten.admin.ch/api/v1/stations?format=json → 302 to HTML
  - https://api.hydrodaten.admin.ch/v1/stations → DNS resolution failed
  - hydrodaten.admin.ch → JavaScript SPA, no server-rendered data

The BAFU hydrology portal (hydrodaten.admin.ch) is a JavaScript single-page
application that does not expose a documented public REST API. The data is
loaded via internal XHR requests that are not stable for third-party use.

Potential alternative: data.geo.admin.ch has some BAFU hydrology WMS layers
but these are static maps, not time-series data.

This module is a placeholder for when BAFU publishes a documented public API.

See: https://github.com/LNKtwo/ha-meteoswiss/issues
"""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

# TODO: Implement when BAFU publishes a documented public API.
# Potential approaches for future investigation:
# 1. Check if hydrodaten.admin.ch has an undocumented REST API by inspecting
#    network requests on the website
# 2. Contact BAFU for API access
# 3. Use the BAFU FOEN (Federal Office for the Environment) Open Government Data
#    portal if data becomes available
