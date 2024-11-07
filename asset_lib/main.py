import json
import socket
import argparse
import time

from asset_lib.impl.comm.udp_comm import UdpComm
from asset_lib.impl.sync_manager import SyncManager

def load_config(config_path):
    try:
        with open(config_path, 'r') as file:
            config_data = json.load(file)
            print("Config loaded successfully:", config_data)
            return config_data
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from {config_path}: {e}")
        return {}

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception as e:
        print("Error obtaining local IP address:", e)
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip

def start_service(my_ip: str, ar_ip: str, web_ip: str, recv_port: int, send_port: int) -> SyncManager:
    # UdpCommインスタンスを作成
    udp_service = UdpComm(recv_ip=my_ip, recv_port=recv_port, send_ip=ar_ip, send_port=send_port)

    # SyncManagerを初期化
    sync_manager = SyncManager(web_ip, udp_service, heartbeat_timeout_sec=5)
    sync_manager.start_service()
    return sync_manager

def main():
    parser = argparse.ArgumentParser(description="Load configuration for Hakoniwa AR Bridge")
    parser.add_argument('--config', type=str, default="config/ar_bridge_config.json",
                        help="Path to the configuration file (default: config/ar_bridge_config.json)")
    parser.add_argument('--my_ip', type=str, help="IP address of the My PC")
    parser.add_argument('--ar_ip', type=str, help="IP address of the AR device")
    parser.add_argument('--web_ip', type=str, help="IP address of the Web server")

    args = parser.parse_args()

    # Load the configuration file
    config = load_config(args.config)

    # IPアドレスとポートを取得、引数が指定されていない場合はデフォルトを利用
    my_ip = args.my_ip if args.my_ip else get_local_ip()
    ar_ip = args.ar_ip if args.ar_ip else config.get("ar_ip", "127.0.0.1")
    web_ip = args.web_ip if args.web_ip else config.get("web_ip", "127.0.0.1")
    recv_port = config.get("recv_port", 38528)
    send_port = config.get("send_port", 38528)

    print(f"Using My IP: {my_ip}")
    print(f"Using AR IP: {ar_ip}")
    print(f"Using Web Server IP: {web_ip}")
    print(f"Receiving on port: {recv_port}, Sending on port: {send_port}")
    print(f"json: {config}")

    # SyncManagerサービスの開始
    sync_manager = start_service(my_ip, ar_ip, web_ip, recv_port, send_port)
    try:
        while True:
            status = sync_manager.get_sync_status()
            print(f"\rsync_status: {status}", end='', flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nService stopped by user.")

if __name__ == "__main__":
    main()
