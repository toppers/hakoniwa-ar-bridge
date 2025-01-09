import json
import argparse
import os
import logging
import threading

class HakoniwaARBridgeServiceContainer:
    def __init__(self, node_path: str):
        #get directory path
        self.node_path = node_path
        self.node_dir = os.path.dirname(node_path)
        print(f'node_dir: {self.node_dir}')
        self.node = self.load_config(node_path)
        print(f'node: {self.node}')
        self.services = []
        for node in self.node['nodes']:
            print(f'node: {node}')
            config_path = os.path.join(self.node_dir, node['path'])
            print(f'config_path: {config_path}')
            if node['type'] == 'device':
                from asset_lib.impl.device.hakoniwa_ar_bridge_service_device import HakoniwaARBridgeServiceDevice
                self.services.append(
                    HakoniwaARBridgeServiceDevice(
                        config_path, 
                        self.node['bridge_ip'], 
                        self.node['ar_port'], 
                        self.node['web_ip']))
            elif node['type'] == 'local':
                #TODO 箱庭のインストールが必要となるため、ローカルでインポートしています。
                from asset_lib.impl.local.hakoniwa_ar_bridge_service_local import HakoniwaARBridgeServiceLocal
                self.services.append(
                    HakoniwaARBridgeServiceLocal(
                        config_path, 
                        self.node['bridge_ip'], 
                        self.node['ar_ip'], 
                        self.node['web_ip']))
            else:
                logging.error("Error: Unknown node type %s", node['type'])

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as file:
                config_data = json.load(file)
                logging.info("Node loaded successfully: %s", config_data)
                return config_data
        except FileNotFoundError:
            logging.error("Error: Node file not found at %s", config_path)
            return {}
        except json.JSONDecodeError as e:
            logging.error("Error: Failed to decode JSON from %s: %s", config_path, e)
            return {}

    def start_service(self):
        for service in self.services:
            service.start_service()
    
    def run(self):
        # サービス毎にスレッドを起動して実行
        threads = []
        for service in self.services:
            # スレッド起動
            thread = threading.Thread(target=service.run, daemon=True)
            thread.start()
            threads.append(thread)
        # スレッド待ち合わせ
        for thread in threads:
            thread.join()


def main():
    parser = argparse.ArgumentParser(description="Load configuration for Hakoniwa AR Bridge")
    parser.add_argument('--node', type=str, default="asset_lib/config/node.json",
                        help="Path to the node definition file (default: asset_lib/config/node.json)")
    args = parser.parse_args()

    service_container = HakoniwaARBridgeServiceContainer(args.node)
    # サービスの開始
    service_container.start_service()

    print("Hakoniwa AR Bridge started.")
    service_container.run()

if __name__ == "__main__":
    main()
