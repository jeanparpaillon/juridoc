#!/usr/bin/env python3
import logging
import sys

import juridoc

logger = logging.getLogger(__name__)

if __name__ == "__main__":
	logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
	sys.exit(juridoc.run())
