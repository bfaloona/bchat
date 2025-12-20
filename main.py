import configparser

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def main():
    config = load_config()
    print("Configuration loaded:", config["DEFAULT"])

if __name__ == "__main__":
    main()
