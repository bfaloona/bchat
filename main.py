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
    """
    Main async entry point for the application.
    
    Sets up configuration, logging, and runs the REPL loop.
    Ensures proper cleanup of async resources on exit.
    """
    config = load_config()
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("Application startup")

    session = Session(config)
    logger.info(f"Session initialized with model: {session.model}, temperature: {session.temperature}")

    # Load MCP configuration and connect to autoconnect servers
    try:
        session.mcp_manager.load_config()
        await session.mcp_manager.connect_autoconnect_servers()
        logger.info("MCP servers initialized")
    except Exception as e:
        logger.warning(f"MCP initialization failed: {e}")

    repl = Repl(session)

    try:
        await repl.run()
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        raise
    finally:
        # Ensure proper cleanup of async resources
        if session.client:
            logger.debug("Closing AsyncOpenAI client")
            await session.client.close()
        # Cleanup MCP connections
        if session.mcp_manager:
            logger.debug("Cleaning up MCP connections")
            await session.mcp_manager.cleanup()
        logger.info("Application shutdown")

def main():
    """
    Synchronous wrapper for the async main function.
    
    Uses asyncio.run() to manage the event loop lifecycle.
    """
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print("\nShutdown requested...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise

if __name__ == "__main__":
    main()
