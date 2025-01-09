import threading
import time
from typing import Dict, Any
from asset_lib.impl.comm.packet import EventRequest, HeartBeatRequest, PositioningRequest
from asset_lib.impl.comm.udp_comm import UdpComm
from asset_lib.impl.sync_manager_base import SyncManagerBaseService
from asset_lib.impl.sync_state import SyncStateManagement, SyncState
from asset_lib.sync_interface import SyncManagerInterface

class SyncManagerDevice(SyncManagerInterface):
    def __init__(self, web_ip: str, udp_service: UdpComm, heartbeat_timeout_sec: int, positioning_speed, position, rotation):
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
        self.service = SyncManagerBaseService(self.state_management, web_ip, udp_service, heartbeat_timeout_sec, positioning_speed, self.saved_position_packet.data)

    def update_saved_position_packet(self, position, rotation) -> None:
        self.position = position
        self.orientation = rotation
        self.service.update_saved_position_packet(self.position, self.orientation)

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
            self.state_management.start_play()
        except Exception as e:
            print(f"Error starting play: {e}")

    def reset(self) -> None:
        try:
            print("EVENT: reset")
            self.state_management.disconnect_or_reset()
            self.udp_service.reset()
        except Exception as e:
            print(f"Error during reset: {e}")

    def is_reset(self) -> bool:
        try:
            packet = self.udp_service.get_packet('reset')
            if packet:
                return True
            return False
        except Exception as e:
            print(f"Error checking reset: {e}")
            return False

    def is_play_start(self) -> bool:
        try:
            # through reset event
            _ = self.udp_service.get_packet('reset')
            packet = self.udp_service.get_packet('play_start')
            if packet:
                return True
            return False
        except Exception as e:
            print(f"Error checking play start: {e}")
            return False

    def update_position(self) -> None:
        try:
            # through reset event
            _ = self.udp_service.get_packet('reset')
            packet = self.udp_service.get_packet('position')
            if packet:
                self.position = packet.data['position']
                self.orientation = packet.data['orientation']
                self.update_saved_position_packet(self.position, self.orientation)
                print(f"Updating position to {self.position} and orientation to {self.orientation}")
                return True
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
