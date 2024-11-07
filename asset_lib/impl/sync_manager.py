import threading
import time
from typing import Dict, Any
from asset_lib.impl.comm.packet import HeartBeatRequest, PositioningRequest
from asset_lib.impl.comm.udp_comm import UdpComm
from sync_interface import SyncManagerInterface
from sync_state import SyncStateManagement, SyncState

class SyncManagerBaseService:
    def __init__(self, state_management: SyncStateManagement, web_ip: str, udp_service: UdpComm, heartbeat_timeout_sec: int = 5):
        self.state_management = state_management
        self.ar_device_is_alive = False
        self.web_ip = web_ip
        self.udp_service = udp_service
        self.heartbeat_timeout_sec = heartbeat_timeout_sec

    def run(self):
        packet = HeartBeatRequest(self.web_ip)
        self.udp_service.send_packet(packet)
        if time.time() - self.udp_service.get_last_recv_time() > self.heartbeat_timeout_sec:
            print("Heartbeat timeout: assuming AR device is disconnected.")
            self.ar_device_is_alive = False
            self.state_management.disconnect_or_reset()

class SyncManager(SyncManagerInterface):
    def __init__(self, web_ip: str, udp_service: UdpComm, heartbeat_timeout_sec: int = 5):
        self.state_management = SyncStateManagement()
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.orientation = {"x": 0.0, "y": 0.0, "z": 0.0}        
        self.running = False
        self.thread = None
        self.udp_service = udp_service
        self.service = SyncManagerBaseService(self.state_management, web_ip, udp_service, heartbeat_timeout_sec)

    def start_service(self) -> None:
        if not self.running:
            self.udp_service.start_receiving()
            self.running = True
            self.thread = threading.Thread(target=self._run_service, daemon=True)
            self.thread.start()
            print("SyncManager service started.")

    def _run_service(self) -> None:
        while self.running:
            if self.service:
                self.service.run()
            else:
                print("No service defined for the current state.")
            time.sleep(1)

    def stop_service(self) -> None:
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            self.udp_service.stop()
            print("SyncManager service stopped.")

    def start_play(self) -> None:
        self.state_management.start_play()

    def reset(self) -> None:
        self.state_management.disconnect_or_reset()

    def update_position(self, position: Dict[str, float], orientation: Dict[str, float]) -> None:
        if self.state_management.state == SyncState.POSITIONING:
            packet = PositioningRequest("unity", position, orientation)
            self.udp_service.send_packet(packet)
            self.position = position
            self.orientation = orientation
            print(f"Updating position to {position} and orientation to {orientation}")

    def get_ar_status(self) -> Dict[str, Any]:
        return {"status": self.state_management.state.name, "position": self.position, "orientation": self.orientation}

    def get_sync_status(self) -> Dict[str, Any]:
        return {"sync_state": self.state_management.state.name}
