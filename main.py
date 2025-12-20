import configparser
import logging
import json
from openai import OpenAI

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
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

    api_key = config["DEFAULT"].get("api_key")
    if not api_key:
        msg = "Error: API key not found in config.ini"
        print(msg)
        logger.error(msg)
        return

    system_instruction = config["DEFAULT"].get("system_instruction")
    if not system_instruction:
        msg = "Error: System Instruction not found in config.ini"
        print(msg)
        logger.error(msg)
        return

    client = OpenAI(api_key=api_key)

    try:
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": "How many fingers are there, in total?"}
        ]

        # Log truncated user prompt at INFO level
        user_content = messages[1]["content"]
        truncated_content = (user_content[:20] + '..') if len(user_content) > 20 else user_content
        logger.info(f"User prompt: {truncated_content}")

        # Log full request at DEBUG level
        logger.debug(f"Full request messages: {json.dumps(messages)}")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        print("Response from OpenAI:")
        content = response.choices[0].message.content
        print(content)

        logger.info("Received response from OpenAI")
        logger.debug(f"Full response: {content}")

    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()
