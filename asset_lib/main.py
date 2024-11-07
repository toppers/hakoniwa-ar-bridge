import json
import socket
import argparse
import time
import logging
from asset_lib.impl.comm.udp_comm import UdpComm
from asset_lib.impl.drivers.joystick_input_handler import JoystickInputHandler
from asset_lib.impl.sync_manager import SyncManager

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HakoniwaARBridgeService:
    def __init__(self, config_path: str, my_ip: str, ar_ip: str, web_ip: str):
        # 設定ファイルの読み込み
        self.config = self.load_config(config_path)
        self.my_ip = my_ip or self.get_local_ip()
        self.ar_ip = ar_ip or self.config.get("ar_ip", "127.0.0.1")
        self.web_ip = web_ip or self.config.get("web_ip", "127.0.0.1")
        self.recv_port = self.config.get("recv_port", 48528)
        self.send_port = self.config.get("send_port", 38528)
        self.output_file = self.config.get("output_file",config_path)

        # UDP通信サービスとSyncManagerの初期化
        self.udp_service = UdpComm(recv_ip=self.my_ip, recv_port=self.recv_port, send_ip=self.ar_ip, send_port=self.send_port)
        self.sync_manager = SyncManager(self.web_ip, self.udp_service, heartbeat_timeout_sec=5)
        self.joystick_input = JoystickInputHandler(self.config['position'], self.config['rotation'], self.sync_manager, self.save_to_json)

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as file:
                config_data = json.load(file)
                logging.info("Config loaded successfully: %s", config_data)
                return config_data
        except FileNotFoundError:
            logging.error("Error: Config file not found at %s", config_path)
            return {}
        except json.JSONDecodeError as e:
            logging.error("Error: Failed to decode JSON from %s: %s", config_path, e)
            return {}

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except Exception as e:
            logging.error("Error obtaining local IP address: %s", e)
            local_ip = "127.0.0.1"
        finally:
            s.close()
        return local_ip

    def save_to_json(self, position, rotation):
        """指定したファイルに位置と回転情報を保存"""
        data = {
            "web_ip": self.web_ip,
            "ar_ip": self.ar_ip,
            "position": position, 
            "rotation": rotation
        }
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=4)
            #logging.info("Saved current state to %s", self.output_file)
        except IOError as e:
            logging.error("Error saving to file %s: %s", self.output_file, e)

    def start_service(self):
        """SyncManagerサービスの開始"""
        try:
            self.sync_manager.start_service()
            logging.info("Using My IP: %s", self.my_ip)
            logging.info("Using AR IP: %s", self.ar_ip)
            logging.info("Using Web Server IP: %s", self.web_ip)
            logging.info("Receiving on port: %d, Sending on port: %d", self.recv_port, self.send_port)
            logging.info("Config: %s", self.config)
        except Exception as e:
            logging.error("Error starting SyncManager service: %s", e)

    def run(self):
        """サービスのメインループ"""
        try:
            while True:
                status = self.sync_manager.get_sync_status()
                logging.info("sync_status: %s", status)
                if status == "POSITIONING":
                    ret = self.joystick_input.handle_input()
                    if ret == True:
                        self.sync_manager.start_play()
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Service stopped by user.")
            self.sync_manager.stop_service()

def main():
    parser = argparse.ArgumentParser(description="Load configuration for Hakoniwa AR Bridge")
    parser.add_argument('--config', type=str, default="config/ar_bridge_config.json",
                        help="Path to the configuration file (default: config/ar_bridge_config.json)")
    parser.add_argument('--my_ip', type=str, help="IP address of the My PC")
    parser.add_argument('--ar_ip', type=str, help="IP address of the AR device")
    parser.add_argument('--web_ip', type=str, help="IP address of the Web server")

    args = parser.parse_args()

    # サービスの開始
    service = HakoniwaARBridgeService(args.config, args.my_ip, args.ar_ip, args.web_ip)
    service.start_service()
    service.run()

if __name__ == "__main__":
    main()
