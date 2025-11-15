"""
OVN (Open Virtual Network) management service for Layer 2-7 networking
"""
import logging
import subprocess
import json
import uuid as uuid_lib
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class OVNManager:
    """Manager for OVN operations"""

    def __init__(self, nb_db: str, sb_db: str):
        """Initialize OVN manager

        Args:
            nb_db: OVN Northbound database connection string
            sb_db: OVN Southbound database connection string
        """
        self.nb_db = nb_db
        self.sb_db = sb_db

    def _run_ovn_nbctl(self, args: List[str]) -> str:
        """Run ovn-nbctl command"""
        cmd = ["ovn-nbctl", f"--db={self.nb_db}"] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"ovn-nbctl command failed: {e.stderr}")
            raise Exception(f"OVN command failed: {e.stderr}")

    def _run_ovn_sbctl(self, args: List[str]) -> str:
        """Run ovn-sbctl command"""
        cmd = ["ovn-sbctl", f"--db={self.sb_db}"] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"ovn-sbctl command failed: {e.stderr}")
            raise Exception(f"OVN command failed: {e.stderr}")

    # Logical Switch operations
    def create_logical_switch(self, name: str, subnet: str) -> str:
        """Create a logical switch"""
        try:
            ls_uuid = str(uuid_lib.uuid4())

            # Create logical switch
            self._run_ovn_nbctl([
                "ls-add", name,
                "--",
                "set", "logical_switch", name, f"external_ids:uuid={ls_uuid}"
            ])

            logger.info(f"Created logical switch: {name}")
            return ls_uuid

        except Exception as e:
            logger.error(f"Failed to create logical switch: {e}")
            raise

    def delete_logical_switch(self, name: str) -> bool:
        """Delete a logical switch"""
        try:
            self._run_ovn_nbctl(["ls-del", name])
            logger.info(f"Deleted logical switch: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete logical switch: {e}")
            raise

    def list_logical_switches(self) -> List[Dict[str, Any]]:
        """List all logical switches"""
        try:
            output = self._run_ovn_nbctl(["--format=json", "ls-list"])
            if not output:
                return []

            switches = []
            # Parse output (simplified)
            lines = output.split('\n')
            for line in lines:
                if line.strip():
                    # Extract switch name
                    parts = line.split()
                    if len(parts) >= 2:
                        switches.append({
                            "name": parts[1].strip('()'),
                            "uuid": parts[0]
                        })

            return switches

        except Exception as e:
            logger.error(f"Failed to list logical switches: {e}")
            return []

    # Logical Router operations
    def create_logical_router(self, name: str) -> str:
        """Create a logical router"""
        try:
            lr_uuid = str(uuid_lib.uuid4())

            # Create logical router
            self._run_ovn_nbctl([
                "lr-add", name,
                "--",
                "set", "logical_router", name, f"external_ids:uuid={lr_uuid}"
            ])

            logger.info(f"Created logical router: {name}")
            return lr_uuid

        except Exception as e:
            logger.error(f"Failed to create logical router: {e}")
            raise

    def delete_logical_router(self, name: str) -> bool:
        """Delete a logical router"""
        try:
            self._run_ovn_nbctl(["lr-del", name])
            logger.info(f"Deleted logical router: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete logical router: {e}")
            raise

    def list_logical_routers(self) -> List[Dict[str, Any]]:
        """List all logical routers"""
        try:
            output = self._run_ovn_nbctl(["--format=json", "lr-list"])
            if not output:
                return []

            routers = []
            lines = output.split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        routers.append({
                            "name": parts[1].strip('()'),
                            "uuid": parts[0]
                        })

            return routers

        except Exception as e:
            logger.error(f"Failed to list logical routers: {e}")
            return []

    def connect_switch_to_router(
        self,
        switch_name: str,
        router_name: str,
        ip_address: str
    ) -> bool:
        """Connect a logical switch to a router"""
        try:
            port_name = f"{switch_name}-{router_name}"

            # Create router port
            self._run_ovn_nbctl([
                "lrp-add", router_name, port_name, "00:00:00:00:00:01", ip_address
            ])

            # Create switch port
            self._run_ovn_nbctl([
                "lsp-add", switch_name, f"{port_name}-sw"
            ])

            # Set switch port type to router
            self._run_ovn_nbctl([
                "lsp-set-type", f"{port_name}-sw", "router"
            ])

            # Set options
            self._run_ovn_nbctl([
                "lsp-set-options", f"{port_name}-sw", f"router-port={port_name}"
            ])

            logger.info(f"Connected switch {switch_name} to router {router_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect switch to router: {e}")
            raise

    # ACL operations
    def create_acl(
        self,
        entity_type: str,
        entity_name: str,
        direction: str,
        priority: int,
        match: str,
        action: str
    ) -> str:
        """Create an ACL rule

        Args:
            entity_type: "switch" or "port_group"
            entity_name: Name of the entity
            direction: "from-lport" or "to-lport"
            priority: Priority (0-32767)
            match: Match expression
            action: "allow", "allow-related", "drop", or "reject"
        """
        try:
            acl_uuid = str(uuid_lib.uuid4())

            cmd_type = "ls" if entity_type == "switch" else "pg"

            self._run_ovn_nbctl([
                f"--id=@acl", "create", "acl",
                f"direction={direction}",
                f"priority={priority}",
                f"match=\"{match}\"",
                f"action={action}",
                f"external_ids:uuid={acl_uuid}",
                "--",
                "add", f"logical_{entity_type}", entity_name, "acls", "@acl"
            ])

            logger.info(f"Created ACL on {entity_name}")
            return acl_uuid

        except Exception as e:
            logger.error(f"Failed to create ACL: {e}")
            raise

    def delete_acl(self, entity_name: str, direction: str, priority: int, match: str) -> bool:
        """Delete an ACL rule"""
        try:
            self._run_ovn_nbctl([
                "acl-del", entity_name, direction, str(priority), f"\"{match}\""
            ])

            logger.info(f"Deleted ACL from {entity_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete ACL: {e}")
            raise

    # Load Balancer operations (Layer 4-7)
    def create_load_balancer(
        self,
        name: str,
        protocol: str,
        vip: str,
        backends: List[str]
    ) -> str:
        """Create a load balancer

        Args:
            name: Load balancer name
            protocol: "tcp", "udp", or "sctp"
            vip: Virtual IP:port (e.g., "10.0.1.100:80")
            backends: List of backend IP:port (e.g., ["10.0.1.10:80", "10.0.1.11:80"])
        """
        try:
            lb_uuid = str(uuid_lib.uuid4())
            backends_str = ",".join(backends)

            self._run_ovn_nbctl([
                "lb-add", name, vip, backends_str, protocol,
                "--",
                "set", "load_balancer", name, f"external_ids:uuid={lb_uuid}"
            ])

            logger.info(f"Created load balancer: {name}")
            return lb_uuid

        except Exception as e:
            logger.error(f"Failed to create load balancer: {e}")
            raise

    def delete_load_balancer(self, name: str) -> bool:
        """Delete a load balancer"""
        try:
            self._run_ovn_nbctl(["lb-del", name])
            logger.info(f"Deleted load balancer: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete load balancer: {e}")
            raise

    def add_load_balancer_to_switch(self, lb_name: str, switch_name: str) -> bool:
        """Add a load balancer to a logical switch"""
        try:
            self._run_ovn_nbctl([
                "ls-lb-add", switch_name, lb_name
            ])

            logger.info(f"Added load balancer {lb_name} to switch {switch_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add load balancer to switch: {e}")
            raise

    def list_load_balancers(self) -> List[Dict[str, Any]]:
        """List all load balancers"""
        try:
            output = self._run_ovn_nbctl(["--format=json", "lb-list"])
            if not output:
                return []

            lbs = []
            lines = output.split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        lbs.append({
                            "name": parts[1].strip('()'),
                            "uuid": parts[0]
                        })

            return lbs

        except Exception as e:
            logger.error(f"Failed to list load balancers: {e}")
            return []

    # DHCP operations
    def configure_dhcp(
        self,
        switch_name: str,
        subnet: str,
        gateway: str,
        dns_servers: List[str],
        dhcp_range_start: str,
        dhcp_range_end: str
    ) -> bool:
        """Configure DHCP for a logical switch"""
        try:
            # Create DHCP options
            dns_str = ",".join(dns_servers) if dns_servers else ""

            self._run_ovn_nbctl([
                "dhcp-options-create", subnet,
                "--",
                "dhcp-options-set-options",
                f"server_id={gateway}",
                f"server_mac=00:00:00:00:00:01",
                f"lease_time=3600",
                f"router={gateway}",
                f"dns_server={{{dns_str}}}" if dns_str else ""
            ])

            logger.info(f"Configured DHCP for switch {switch_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to configure DHCP: {e}")
            raise

    def get_topology(self) -> Dict[str, Any]:
        """Get network topology"""
        try:
            topology = {
                "switches": self.list_logical_switches(),
                "routers": self.list_logical_routers(),
                "load_balancers": self.list_load_balancers()
            }

            return topology

        except Exception as e:
            logger.error(f"Failed to get topology: {e}")
            return {"switches": [], "routers": [], "load_balancers": []}
