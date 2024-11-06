import json
import os
import argparse

def load_config(config_path):
    try:
        with open(config_path, 'r') as file:
            config_data = json.load(file)
            print("Config loaded successfully:", config_data)
            return config_data
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from {config_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Load configuration for Hakoniwa AR Bridge")
    parser.add_argument('--config', type=str, default="config/ar_bridge_config.json",
                        help="Path to the configuration file (default: config/ar_bridge_config.json)")
    parser.add_argument('--ar_ip', type=str, help="IP address of the AR device")
    parser.add_argument('--web_ip', type=str, help="IP address of the Web server")

    args = parser.parse_args()

    # Load the configuration file
    config = load_config(args.config)

    # AR and Web IPs: Override from command-line arguments if provided
    ar_ip = args.ar_ip if args.ar_ip else config.get("ar_ip")
    web_ip = args.web_ip if args.web_ip else config.get("web_ip")

    print(f"Using AR IP: {ar_ip}")
    print(f"Using Web Server IP: {web_ip}")
    print(f"json: {config}")

if __name__ == "__main__":
    main()
