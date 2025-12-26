import asyncio
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

async def async_main():
    """Main async entry point for the application."""
    config = load_config()
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("Application startup")

    session = Session(config)
    logger.info(f"Session initialized with model: {session.model}, temperature: {session.temperature}")

    repl = Repl(session)

    await repl.run()

def main():
    """Synchronous wrapper for the async main function."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
