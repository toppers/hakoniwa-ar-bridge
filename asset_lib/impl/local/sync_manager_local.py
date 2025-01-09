import threading
import time
from typing import Dict, Any
from asset_lib.impl.comm.packet import EventRequest, HeartBeatRequest, PositioningRequest
from asset_lib.impl.comm.udp_comm import UdpComm
from asset_lib.impl.sync_manager_base import SyncManagerBaseService
from asset_lib.impl.sync_state import SyncStateManagement, SyncState
from asset_lib.sync_interface import SyncManagerInterface

class SyncManagerLocal(SyncManagerInterface):
    def __init__(self, web_ip: str, udp_service: UdpComm, heartbeat_timeout_sec: int, position, rotation):
        self.state_management = SyncStateManagement()
        self.position = {
            "x": position[0],
            "y": position[1],
            "z": position[2]
        }
        self.orientation = {
            "x": rotation[0],
            "y": rotation[1],
            "z": rotation[2]
        }
        self.running = False
        self.thread = None
        self.udp_service = udp_service
        self.saved_position_packet = PositioningRequest("unity", self.position, self.orientation)
        self.service = SyncManagerBaseService(self.state_management, web_ip, udp_service, heartbeat_timeout_sec, self.saved_position_packet.data)

    def start_service(self) -> None:
        if not self.running:
            self.udp_service.start_receiving()
            self.running = True
            self.thread = threading.Thread(target=self._run_service, daemon=True)
            self.thread.start()
            print("SyncManager service started.")

    def _run_service(self) -> None:
        while self.running:
            try:
                if self.service:
                    self.service.run()
                else:
                    print("No service defined for the current state.")                
                time.sleep(1)
            except Exception as e:
                print(f"Error in service run loop: {e}")

    def stop_service(self) -> None:
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            self.udp_service.stop()
            print("SyncManager service stopped.")

    def start_play(self) -> None:
        try:
            print("EVENT: start play")
            packet = EventRequest("play_start")
            self.udp_service.send_packet(packet)
            self.state_management.start_play()
        except Exception as e:
            print(f"Error starting play: {e}")

    def reset(self) -> None:
        try:
            print("EVENT: reset")
            packet = EventRequest("reset")
            self.udp_service.send_packet(packet)
            self.state_management.disconnect_or_reset()
            self.udp_service.reset()
        except Exception as e:
            print(f"Error during reset: {e}")

    def update_position(self, position: Dict[str, float], orientation: Dict[str, float]) -> None:
        try:
            if self.state_management.state == SyncState.POSITIONING:
                packet = PositioningRequest("unity", position, orientation)
                self.udp_service.send_packet(packet)
                self.position = position
                self.orientation = orientation
                #print(f"Updating position to {position} and orientation to {orientation}")
        except Exception as e:
            print(f"Error updating position or sending PositioningRequest: {e}")

    def get_ar_status(self) -> Dict[str, Any]:
        try:
            return {"status": self.state_management.state.name, "position": self.position, "orientation": self.orientation}
        except Exception as e:
            print(f"Error retrieving AR status: {e}")
            return {}

    def get_sync_status(self) -> Dict[str, Any]:
        try:
            return self.state_management.state.name
        except Exception as e:
            print(f"Error retrieving sync status: {e}")
            return {"sync_state": "unknown"}
