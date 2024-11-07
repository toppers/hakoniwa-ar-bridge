from abc import ABC, abstractmethod
from typing import Dict, Any

class SyncManagerInterface(ABC):
    @abstractmethod
    def start_service(self)-> None:
        """Start SyncManager Service."""
        pass
    @abstractmethod
    def stop_service(self)-> None:
        """Stop SyncManager Service."""
        pass

    @abstractmethod
    def start_play(self) -> None:
        """Start the play mode."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset to the initial state."""
        pass

    @abstractmethod
    def update_position(self, position: Dict[str, float], orientation: Dict[str, float]) -> None:
        """Update position and orientation information."""
        pass

    @abstractmethod
    def get_ar_status(self) -> Dict[str, Any]:
        """Get the current status of the device."""
        pass

    @abstractmethod
    def get_sync_status(self) -> Dict[str, Any]:
        """Get the current status of the sync manager."""
        pass

