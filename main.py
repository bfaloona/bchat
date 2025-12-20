import configparser
from openai import OpenAI

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def main():
    config = load_config()
    print("Configuration loaded:", config["DEFAULT"])

    api_key = config["DEFAULT"].get("api_key")
    if not api_key:
        print("Error: API key not found in config.ini")
        return

    system_instruction = config["DEFAULT"].get("system_instruction")
    if not system_instruction:
        print("Error: System Instruction not found in config.ini")
        return

    client = OpenAI(api_key=api_key)

    try:
        print("Sending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": "How many fingers are there, in total?"}
            ]
        )
        print("Response from OpenAI:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
