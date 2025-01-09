import socket
import json
import time
import threading
import argparse

from asset_lib.impl.comm.packet import PositioningRequest

class MockQuest3:
    def __init__(self, mock_type, recv_ip: str, recv_port: int, send_ip: str, send_port: int):
        self.mock_type = mock_type
        self.recv_ip = recv_ip
        self.recv_port = recv_port
        self.send_ip = send_ip
        self.send_port = send_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.recv_ip, self.recv_port))
        self.state = "POSITIONING" 

    def send_heartbeat_response(self):
        """Send periodic heartbeat response to the PC app."""
        packet = {
            "type": "data",
            "data_type": "heartbeat_response",
            "data": {"status": self.state}
        }
        self.sock.sendto(json.dumps(packet).encode('utf-8'), (self.send_ip, self.send_port))

    def send_position_data(self, position, orientation):
        packet = {
            "type": "data",
            "data_type": "position",
            "data": {
                "frame_type": 'unity',
                "position": position,
                "orientation": orientation
            }
        }
        self.sock.sendto(json.dumps(packet).encode('utf-8'), (self.send_ip, self.send_port))

    def handle_packet(self, packet):
        """Handle incoming packets and adjust the state accordingly."""
        packet_type = packet.get("type")
        data_type = packet.get("data_type")
        event_type = packet.get("event_type")

        if packet_type == "data" and data_type == "position":
            # 位置情報を受信した場合、位置合わせモードに遷移
            if self.state == "POSITIONING":
                print("Transitioning to POSITIONING mode.")
                self.state = "POSITIONING"
            print(f"Received position data: {packet['data']}")
        elif packet_type == "data" and data_type == "heartbeat_request":
            # ハートビートリクエストを受信した場合、ハートビートレスポンスを返信
            if self.state == "POSITIONING":
                position = {"x": 0.0, "y": 0.0, "z": 0.0}
                orientation = {"x": 0.0, "y": 0.0, "z": 0.0}
                self.send_position_data(position, orientation)
            #print(f"Received heartbeat request from {packet['data']['ip_address']}.")
            #print(f"Received heartbeat request from {packet['data']['server_udp_port']}.")
            print(f"Received heartbeat request from {packet['data']['saved_position']['position']}.")
            print(f"Received heartbeat request from {packet['data']['saved_position']['orientation']}.")
        elif packet_type == "event":
            if event_type == "play_start":
                # プレイ開始イベントでプレイモードに遷移
                if self.state == "POSITIONING":
                    print("Transitioning to PLAY mode.")
                    self.state = "PLAYING"
            elif event_type == "reset":
                # リセットイベントで待機モードに戻る
                print("Reset received. Returning to POSITIONING mode.")
                self.state = "POSITIONING"

    def receive_loop(self):
        """Receive packets and process them in an infinite loop."""
        while True:
            data, _ = self.sock.recvfrom(1024)
            packet = json.loads(data.decode('utf-8'))
            if packet['type'] == 'data' and packet['data_type'] == "position":
                print(f"Received packet: {packet}")
            self.handle_packet(packet)

    def start(self):
        """Start the Mock app with separate threads for receiving and heartbeat."""
        # Heartbeat thread
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        # Receiving loop
        self.receive_loop()

    def heartbeat_loop(self):
        """Send heartbeat response every second."""
        while True:
            self.send_heartbeat_response()
            #print(f"Sent heartbeat with status: {self.state}")
            time.sleep(1)  # 1秒ごとにハートビートを送信

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Quest3 device")
    parser.add_argument('--type', type=str, default="device", help="Type of the node (default: device)")
    args = parser.parse_args()
    recv_ip = "0.0.0.0"  # 受信側のIPアドレス
    recv_port = 38528    # 受信ポート番号
    send_ip = "127.0.0.1"  # PCアプリ側のIPアドレス
    send_port = 48528    # 送信ポート番号

    print(f"Starting MockQuest3 with recv_ip={recv_ip}, recv_port={recv_port}, send_ip={send_ip}, send_port={send_port}")
    mock_quest3 = MockQuest3(args.type, recv_ip, recv_port, send_ip, send_port)
    mock_quest3.start()
