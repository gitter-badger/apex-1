#!/usr/bin/env python
# -*- coding: utf-8 -*-

# APRS Python Module.

"""
APRS Python Module.
~~~~


:author: Jeffrey Phillips Freeman WI2ARD <freemo@gmail.com>
:copyright: Copyright 2016 Syncleus, Inc. and contributors
:license: Apache License, Version 2.0
:source: <https://github.com/syncleus/apex>

"""

import logging
from .classes import APRSKISS
from .classes import APRS


# Set default logging handler to avoid "No handler found" warnings.
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        """Default logging handler to avoid "No handler found" warnings."""
        def emit(self, record):
            """Default logging handler to avoid "No handler found" warnings."""
            pass

logging.getLogger(__name__).addHandler(NullHandler())
