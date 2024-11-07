import socket
import json
import threading
from asset_lib.impl.comm.packet import BasePacket, HeartBeatRequest, HeartBeatResponse, EventRequest, PositioningRequest
from typing import Dict, Optional, Type
from time import sleep, time

class UdpComm:
    def __init__(self, recv_ip: str, recv_port: int, send_ip: Optional[str] = None, send_port: Optional[int] = None):
        self.recv_ip = recv_ip
        self.recv_port = recv_port
        self.send_ip = send_ip if send_ip else recv_ip  # 送信IPが指定されていない場合は受信用のIPを使用
        self.send_port = send_port if send_port else recv_port  # 送信ポートが指定されていない場合は受信用のポートを使用

        self.buffer: Dict[str, Optional[BasePacket]] = {}
        self.lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.recv_ip, self.recv_port))
        self.running = True
        self.last_recv_time = 0

        # data_typeに対応するパケットクラスのマッピング
        self.packet_classes = {
            "heartbeat_request": HeartBeatRequest,
            "heartbeat_response": HeartBeatResponse,
            "event": EventRequest,
            "position": PositioningRequest
        }

    def get_last_recv_time(self):
        return self.last_recv_time

    def send_packet(self, packet: BasePacket):
        """Send a packet as a JSON string via UDP."""
        json_data = packet.to_json()
        self.sock.sendto(json_data.encode('utf-8'), (self.send_ip, self.send_port))

    def receive_loop(self):
        """Continuously listen for incoming packets, parse, and buffer the latest packet by type."""
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                #print("data: ", data)
                json_data = data.decode('utf-8')
                base_packet = BasePacket.from_json(json_data)
                queue_name = None
                if base_packet.type == "data":
                    queue_name = base_packet.data_type
                elif base_packet.type == "event":
                    queue_name = base_packet.event_type
                else:
                    print("ERROR: invalid packet type: ", base_packet.type)
                    continue
                packet_class = self.packet_classes.get(queue_name, BasePacket)
                packet = packet_class.from_json(json_data)

                # Buffer the latest packet by its type
                with self.lock:
                    self.last_recv_time = time()
                    self.buffer[queue_name] = packet

            except Exception as e:
                print(f"Error receiving data: {e}")
                sleep(0.1)  # To avoid high CPU usage on failure

    def start_receiving(self):
        """Start the receive loop in a separate thread."""
        self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()

    def reset(self):
        """Clear the buffer and reset last received time."""
        with self.lock:
            self.sock.close()
            self.buffer.clear()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.recv_ip, self.recv_port))
            self.last_recv_time = 0
        print("Buffer and last receive time reset.")

    def stop(self):
        """Stop the receiving loop and close the socket."""
        self.running = False
        self.receive_thread.join()
        self.sock.close()
