import socket
import json
import threading
from packet import BasePacket, HeartBeatRequest, HeartBeatResponse, EventRequest, PositioningRequest
from typing import Dict, Optional, Type
from time import sleep, time

class UdpComm:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.buffer: Dict[str, Optional[BasePacket]] = {}
        self.lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
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
        self.sock.sendto(json_data.encode('utf-8'), (self.ip, self.port))

    def receive_loop(self):
        """Continuously listen for incoming packets, parse, and buffer the latest packet by type."""
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
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

    def get_latest_packet(self, packet_type: str) -> Optional[BasePacket]:
        """Retrieve the latest packet for a given packet type."""
        with self.lock:
            return self.buffer.get(packet_type)

    def stop(self):
        """Stop the receiving loop and close the socket."""
        self.running = False
        self.receive_thread.join()
        self.sock.close()
