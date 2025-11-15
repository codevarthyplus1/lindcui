"""
OVS (Open vSwitch) management service
"""
import logging
import subprocess
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OVSManager:
    """Manager for OVS operations"""

    def __init__(self):
        """Initialize OVS manager"""
        pass

    def _run_ovs_vsctl(self, args: List[str]) -> str:
        """Run ovs-vsctl command"""
        cmd = ["ovs-vsctl"] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"ovs-vsctl command failed: {e.stderr}")
            raise Exception(f"OVS command failed: {e.stderr}")

    def _run_ovs_ofctl(self, args: List[str]) -> str:
        """Run ovs-ofctl command"""
        cmd = ["ovs-ofctl"] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"ovs-ofctl command failed: {e.stderr}")
            raise Exception(f"OVS command failed: {e.stderr}")

    def list_bridges(self) -> List[str]:
        """List all OVS bridges"""
        try:
            output = self._run_ovs_vsctl(["list-br"])
            if not output:
                return []

            return [bridge.strip() for bridge in output.split('\n') if bridge.strip()]

        except Exception as e:
            logger.error(f"Failed to list bridges: {e}")
            return []

    def create_bridge(self, bridge_name: str) -> bool:
        """Create an OVS bridge"""
        try:
            self._run_ovs_vsctl(["add-br", bridge_name])
            logger.info(f"Created OVS bridge: {bridge_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create bridge: {e}")
            raise

    def delete_bridge(self, bridge_name: str) -> bool:
        """Delete an OVS bridge"""
        try:
            self._run_ovs_vsctl(["del-br", bridge_name])
            logger.info(f"Deleted OVS bridge: {bridge_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete bridge: {e}")
            raise

    def add_port(self, bridge_name: str, port_name: str) -> bool:
        """Add a port to a bridge"""
        try:
            self._run_ovs_vsctl(["add-port", bridge_name, port_name])
            logger.info(f"Added port {port_name} to bridge {bridge_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add port: {e}")
            raise

    def delete_port(self, bridge_name: str, port_name: str) -> bool:
        """Delete a port from a bridge"""
        try:
            self._run_ovs_vsctl(["del-port", bridge_name, port_name])
            logger.info(f"Deleted port {port_name} from bridge {bridge_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete port: {e}")
            raise

    def list_ports(self, bridge_name: str) -> List[str]:
        """List all ports on a bridge"""
        try:
            output = self._run_ovs_vsctl(["list-ports", bridge_name])
            if not output:
                return []

            return [port.strip() for port in output.split('\n') if port.strip()]

        except Exception as e:
            logger.error(f"Failed to list ports: {e}")
            return []

    def get_bridge_info(self, bridge_name: str) -> Dict[str, Any]:
        """Get detailed bridge information"""
        try:
            ports = self.list_ports(bridge_name)

            # Get OpenFlow version
            of_version = self._run_ovs_vsctl([
                "get", "bridge", bridge_name, "protocols"
            ])

            return {
                "name": bridge_name,
                "ports": ports,
                "openflow_version": of_version
            }

        except Exception as e:
            logger.error(f"Failed to get bridge info: {e}")
            return {"name": bridge_name, "ports": []}

    def show(self) -> str:
        """Show OVS configuration"""
        try:
            return self._run_ovs_vsctl(["show"])
        except Exception as e:
            logger.error(f"Failed to show OVS config: {e}")
            return ""

    def dump_flows(self, bridge_name: str) -> str:
        """Dump OpenFlow flows for a bridge"""
        try:
            return self._run_ovs_ofctl(["dump-flows", bridge_name])
        except Exception as e:
            logger.error(f"Failed to dump flows: {e}")
            return ""

    def get_statistics(self, bridge_name: str) -> Dict[str, Any]:
        """Get bridge statistics"""
        try:
            stats = {}

            # Get port statistics
            output = self._run_ovs_ofctl(["dump-ports", bridge_name])
            stats["ports"] = output

            # Get flow statistics
            output = self._run_ovs_ofctl(["dump-aggregate", bridge_name])
            stats["flows"] = output

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
