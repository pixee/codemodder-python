import logging
import sys

logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("codemodder")
