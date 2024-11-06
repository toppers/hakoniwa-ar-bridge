import json
from typing import Optional, Dict, Any

class BasePacket:
    def __init__(self, packet_type: str, data_type: Optional[str] = None,
                 event_type: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        self.type = packet_type       # "data" or "event"
        self.data_type = data_type    # Only required if type is "data"
        self.event_type = event_type  # Only required if type is "event"
        self.data = data              # Additional data (only if type is "data")

    def to_json(self) -> str:
        """Convert packet to JSON string."""
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str: str) -> 'BasePacket':
        """Parse JSON string and create a packet instance."""
        data = json.loads(json_str)
        packet = cls(
            packet_type=data.get("type"),
            data_type=data.get("data_type"),
            event_type=data.get("event_type"),
            data=data.get("data")
        )
        return packet

class HeartBeatRequest(BasePacket):
    def __init__(self, ip_address: str):
        super().__init__(packet_type="data", data_type="heartbeat_request")
        self.data = {
            "ip_address": ip_address
        }

class HeartBeatResponse(BasePacket):
    def __init__(self, status: str):
        super().__init__(packet_type="data", data_type="heartbeat_response")
        self.data = {
            "status": status
        }

class EventRequest(BasePacket):
    def __init__(self, event_type: str):
        if event_type not in ["play_start", "reset"]:
            raise ValueError("Invalid event type. Expected 'play_start' or 'reset'.")
        super().__init__(packet_type="event", event_type=event_type)


class PositioningRequest(BasePacket):
    def __init__(self, frame_type: str, position: Dict[str, float], orientation: Dict[str, float]):
        super().__init__(packet_type="data", data_type="position")
        self.data = {
            "frame_type": frame_type,
            "position": position,
            "orientation": orientation
        }

