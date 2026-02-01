import os
import logging
from datetime import datetime

# Ensure logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure logger
log_file = os.path.join("logs", f"pos_{datetime.now().strftime('%Y%m')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_info(message):
    logging.info(message)
    print(f"INFO: {message}")

def log_error(message):
    logging.error(message, exc_info=True)
    print(f"ERROR: {message}")
