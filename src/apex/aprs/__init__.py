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

# These imports are for python3 compatability inside python2
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from .aprs_internet_service import AprsInternetService  # noqa: F401
from .aprs_kiss import AprsKiss  # noqa: F401

__author__ = 'Jeffrey Phillips Freeman (WI2ARD)'
__maintainer__ = "Jeffrey Phillips Freeman (WI2ARD)"
__email__ = "jeffrey.freeman@syncleus.com"
__license__ = 'Apache License, Version 2.0'
__copyright__ = 'Copyright 2016, Syncleus, Inc. and contributors'
__credits__ = []

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
