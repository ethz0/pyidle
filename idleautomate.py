#!/usr/bin/env python3
import logging
import sys

from idleautomate.window.window import IcWindow
from idleautomate.arguments import args

logger = logging.getLogger()

BOLD = '\033[1m'
ENDC = '\033[0m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
CYAN = '\033[36m'


if __name__ == '__main__':

    logger = logging.getLogger(__name__)

    if not args.d:
        logging.basicConfig(level=logging.INFO)
    elif args.d:
        logging.basicConfig(level=logging.DEBUG)

    try:
        gamewin = IcWindow()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
