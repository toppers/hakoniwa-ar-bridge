import json
import socket
import time
import os
import logging
from asset_lib.impl.comm.udp_comm import UdpComm
from asset_lib.impl.drivers.joystick_input_handler import JoystickInputHandler
from asset_lib.impl.drivers.rc_utils import RcConfig, StickMonitor
from asset_lib.impl.local.sync_manager_local import SyncManagerLocal
from asset_lib.playing.rc_custom import do_radio_control

# デフォルトのJSONファイルパス
DEFAULT_CONFIG_PATH = "rc_config/ps4-control.json"

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HakoniwaARBridgeServiceLocal:
    def __init__(self, config_path: str, my_ip: str, ar_ip: str, web_ip: str, rc_config_path: str = None):
        # 設定ファイルの読み込み
        self.config = self.load_config(config_path)
        self.my_ip = my_ip or self.get_local_ip()
        self.ar_ip = ar_ip or self.config.get("ar_ip", "127.0.0.1")
        self.web_ip = web_ip or self.config.get("web_ip", "127.0.0.1")
        self.server_udp_port = self.config.get("server_udp_port", 48528)
        self.ar_port = self.config.get("ar_port", 38528)
        self.output_file = self.config.get("output_file",config_path)
        self.custom_config_path = self.config.get("custom_config_path")

        # RcConfigとStickMonitorの初期化
        if rc_config_path is None:
            rc_config_path = os.getenv("RC_CONFIG_PATH", DEFAULT_CONFIG_PATH)
        if not os.path.exists(rc_config_path):
            raise FileNotFoundError(f"Config file not found at '{rc_config_path}'")

        rc_config = RcConfig(rc_config_path)
        print("Controller: ", rc_config_path)
        print("Mode: ", rc_config.config['mode'])
        self.stick_monitor = StickMonitor(rc_config)

        # UDP通信サービスとSyncManagerの初期化
        self.udp_service = UdpComm(recv_ip=self.my_ip, recv_port=self.server_udp_port, send_ip=self.ar_ip, send_port=self.ar_port)
        self.sync_manager = SyncManagerLocal(self.web_ip, self.udp_service, 5, self.config['position'], self.cofnig['rotation'])
        self.joystick_input = JoystickInputHandler(self.config['position'], self.config['rotation'], self.sync_manager, self.save_to_json, self.stick_monitor)

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
            "ar_ip": self.ar_ip,
            "server_udp_port": self.server_udp_port,
            "adjustments": self.config["adjustments"],
            "custom_config_path": self.custom_config_path,
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
            logging.info("Receiving on port: %d, Sending on port: %d", self.server_udp_port, self.ar_port)
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
                    ret = self.joystick_input.handle_input(self.config)
                    if ret == True:
                        self.sync_manager.start_play()
                elif status == "PLAYING":
                    ret = do_radio_control(self.sync_manager, self.custom_config_path, self.stick_monitor)
                    if ret != 0:
                        self.sync_manager.reset()
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Service stopped by user.")
            self.sync_manager.stop_service()