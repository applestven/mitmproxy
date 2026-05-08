# logger.py

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def info(msg):
    logging.info(msg)

def warn(msg):
    logging.warning(msg)