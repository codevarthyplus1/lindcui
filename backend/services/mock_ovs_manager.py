"""
Mock OVS manager for testing without actual OVS installation
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OVSManager:
    """Mock manager for OVS operations"""

    def __init__(self):
        """Initialize mock OVS connection"""
        self.bridges = []
        logger.info("[MOCK] Initialized OVS Manager")

    def list_bridges(self) -> List[str]:
        """List all OVS bridges (mock)"""
        return [b["name"] for b in self.bridges]

    def create_bridge(self, name: str) -> bool:
        """Create an OVS bridge (mock)"""
        if name not in [b["name"] for b in self.bridges]:
            self.bridges.append({"name": name, "ports": []})
            logger.info(f"[MOCK] Created bridge: {name}")
        return True

    def delete_bridge(self, name: str) -> bool:
        """Delete an OVS bridge (mock)"""
        self.bridges = [b for b in self.bridges if b["name"] != name]
        logger.info(f"[MOCK] Deleted bridge: {name}")
        return True

    def add_port(self, bridge: str, port: str) -> bool:
        """Add a port to a bridge (mock)"""
        for b in self.bridges:
            if b["name"] == bridge:
                if port not in b["ports"]:
                    b["ports"].append(port)
                logger.info(f"[MOCK] Added port {port} to bridge {bridge}")
                return True
        return False

    def delete_port(self, bridge: str, port: str) -> bool:
        """Delete a port from a bridge (mock)"""
        for b in self.bridges:
            if b["name"] == bridge:
                if port in b["ports"]:
                    b["ports"].remove(port)
                logger.info(f"[MOCK] Deleted port {port} from bridge {bridge}")
                return True
        return False

    def get_bridge_info(self, name: str) -> Dict[str, Any]:
        """Get bridge information (mock)"""
        for b in self.bridges:
            if b["name"] == name:
                return b
        return {}
