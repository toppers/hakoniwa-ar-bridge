
from asset_lib.impl.comm.packet import HeartBeatRequest
from asset_lib.impl.comm.udp_comm import UdpComm
from asset_lib.impl.sync_state import SyncState, SyncStateManagement
import time

class SyncManagerBaseService:
    def __init__(self, state_management: SyncStateManagement, web_ip: str, udp_service: UdpComm, heartbeat_timeout_sec: int, positioning_speed, saved_position, player, avatars):
        self.state_management = state_management
        self.ar_device_is_alive = False
        self.web_ip = web_ip
        self.udp_service = udp_service
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.positioning_speed = positioning_speed
        self.saved_position = saved_position
        self.player = player
        self.avatars = avatars

    def update_saved_position_packet(self, position, rotation):
        self.saved_position = {
            "frame_type": "unity",
            "position": position,
            "orientation": rotation
        }

    def run(self):
        try:
            packet = HeartBeatRequest(self.web_ip, self.udp_service.get_port(), self.positioning_speed, self.saved_position, self.player, self.avatars)
            #print(f"Sending heartbeat request to {self.web_ip}:{self.udp_service.get_port()}")
            #print(f"Packet: {packet.data}")
            self.udp_service.send_packet(packet)
            #print("last_recv: ", self.udp_service.get_last_recv_time())
            if (self.udp_service.get_last_recv_time() == 0) or (time.time() - self.udp_service.get_last_recv_time() > self.heartbeat_timeout_sec):
                print(f"{self.player['name']} : Heartbeat timeout: assuming AR device is disconnected.")
                self.ar_device_is_alive = False
                self.state_management.disconnect_or_reset()
            else:
                self.ar_device_is_alive = True
            if self.state_management.state == SyncState.WAITING:
                if self.ar_device_is_alive:
                    self.state_management.connect_established()
        except Exception as e:
            #print(f"Error during HeartBeatRequest sending or heartbeat check: {e}")
            pass
