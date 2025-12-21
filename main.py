import configparser
import logging
from session import Session
from repl import Repl

def load_config():
    config = configparser.ConfigParser()
    config.read(['config.ini', 'secrets.ini'])
    return config

def setup_logging(config):
    log_file = config["DEFAULT"].get("log_file", "bchat.log")
    log_level_str = config["DEFAULT"].get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filemode='a'
    )

def main():
    config = load_config()
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("Application startup")
    
    session = Session(config)
    repl = Repl(session)
    
    repl.run()

if __name__ == "__main__":
    main()
