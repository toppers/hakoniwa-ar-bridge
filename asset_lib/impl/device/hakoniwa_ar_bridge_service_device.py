import logging
import json
import time
from asset_lib.impl.comm.udp_comm import UdpComm
from asset_lib.impl.device.sync_manager_device import SyncManagerDevice

class HakoniwaARBridgeServiceDevice:
    def __init__(self, config_path: str, my_ip: str, ar_port: int, web_ip: str):
        self.config = self.load_config(config_path)
        self.my_ip = my_ip
        self.server_udp_port = self.config.get("server_udp_port", 48528)
        self.ar_ip = self.config.get("ar_ip", "127.0.0.1")
        self.ar_port = ar_port
        self.web_ip = web_ip
        self.output_file = self.config.get("output_file",config_path)
        print(f"Config: {self.config}")
        self.udp_service = UdpComm(recv_ip=self.my_ip, recv_port=self.server_udp_port, send_ip=self.ar_ip, send_port=self.ar_port)
        self.sync_manager = SyncManagerDevice(self.web_ip, self.udp_service, 5, self.config['positioning_speed'], self.config['position'], self.config['rotation'], self.config['player'], self.config['avatars'])
        
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


    def save_to_json(self, position, rotation):
        """指定したファイルに位置と回転情報を保存"""
        data = {
            "ar_ip": self.ar_ip,
            "server_udp_port": self.server_udp_port,
            "player": self.config['player'],
            "avatars": self.config['avatars'],
            "positioning_speed": self.config['positioning_speed'],
            "position": [
                position["x"],
                position["y"],
                position["z"]
            ], 
            "rotation": [
                rotation["x"],
                rotation["y"],
                rotation["z"]
            ]
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
            print("Starting SyncManager service.")
            self.sync_manager.start_service()
            print("Using My IP: %s", self.my_ip)
            print("Using AR IP: %s", self.ar_ip)
            print("Using Web Server IP: %s", self.web_ip)
            print("Receiving on port: %d, Sending on port: %d", self.server_udp_port, self.ar_port)
            print("Config: %s", self.config)
        except Exception as e:
            logging.error("Using My IP: %s", self.my_ip)
            logging.error("Using AR IP: %s", self.ar_ip)
            logging.error("Using Web Server IP: %s", self.web_ip)
            logging.error("Error starting SyncManager service: %s", e)

    def run(self):
        """サービスのメインループ"""
        try:
            while True:
                status = self.sync_manager.get_sync_status()
                if status == "POSITIONING":
                    if self.sync_manager.update_position():
                        #print("Updating position.")
                        self.save_to_json(self.sync_manager.position, self.sync_manager.orientation)
                    if self.sync_manager.is_play_start():
                        self.sync_manager.start_play()
                    time.sleep(1)
                elif status == "PLAYING":
                    if self.sync_manager.is_reset():
                        self.sync_manager.reset()
                else:
                    #WAITING
                    time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Service stopped by user.")
            self.sync_manager.stop_service()