import logging
import json

# logging.basicConfig(format="%(message)s", level=logging.DEBUG)
logging.basicConfig(format="%(message)s", level=logging.INFO)

# disable http request logging
# to avoid logging health checks
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


def debug(obj):
    """log object as json if in debug mode"""
    if logging.getLogger().level <= logging.DEBUG:
        logging.debug(json.dumps(obj, indent=2, default=str))


def info(obj):
    """log object as json if in info or debug mode"""
    if logging.getLogger().level <= logging.INFO:
        logging.info(json.dumps(obj, indent=2, default=str))


def llm(input, output):
    """log llm calls to stdout using specific format"""
    payload = {
        "input": input,
        "output": output
    }
    print(f"LLM: {json.dumps(payload, default=str)}")
