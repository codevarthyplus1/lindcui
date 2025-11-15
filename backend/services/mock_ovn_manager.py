"""
Mock OVN manager for testing without actual OVN installation
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class OVNManager:
    """Mock manager for OVN operations"""

    def __init__(self, nb_db: str, sb_db: Optional[str] = None):
        """Initialize mock OVN connection"""
        self.nb_db = nb_db
        self.sb_db = sb_db
        self.switches = []
        self.routers = []
        self.acls = []
        self.load_balancers = []
        logger.info(f"[MOCK] Initialized OVN Manager (NB: {nb_db})")

    def list_switches(self) -> List[Dict[str, Any]]:
        """List all logical switches (mock)"""
        return self.switches

    def list_logical_switches(self) -> List[Dict[str, Any]]:
        """List all logical switches (mock) - alias"""
        return self.list_switches()

    def create_switch(self, name: str, subnet: Optional[str] = None) -> str:
        """Create a logical switch (mock)"""
        switch_uuid = f"switch-{len(self.switches)}-uuid"
        switch = {
            "name": name,
            "uuid": switch_uuid,
            "subnet": subnet,
            "ports": []
        }
        self.switches.append(switch)
        logger.info(f"[MOCK] Created switch: {name}")
        return switch_uuid

    def create_logical_switch(self, name: str, subnet: Optional[str] = None, **kwargs) -> str:
        """Create a logical switch (mock) - alias"""
        return self.create_switch(name, subnet)

    def delete_switch(self, name: str) -> bool:
        """Delete a logical switch (mock)"""
        self.switches = [s for s in self.switches if s["name"] != name]
        logger.info(f"[MOCK] Deleted switch: {name}")
        return True

    def delete_logical_switch(self, name: str) -> bool:
        """Delete a logical switch (mock) - alias"""
        return self.delete_switch(name)

    def list_routers(self) -> List[Dict[str, Any]]:
        """List all logical routers (mock)"""
        return self.routers

    def list_logical_routers(self) -> List[Dict[str, Any]]:
        """List all logical routers (mock) - alias"""
        return self.list_routers()

    def create_router(self, name: str) -> str:
        """Create a logical router (mock)"""
        router_uuid = f"router-{len(self.routers)}-uuid"
        router = {
            "name": name,
            "uuid": router_uuid,
            "ports": []
        }
        self.routers.append(router)
        logger.info(f"[MOCK] Created router: {name}")
        return router_uuid

    def create_logical_router(self, name: str) -> str:
        """Create a logical router (mock) - alias"""
        return self.create_router(name)

    def delete_router(self, name: str) -> bool:
        """Delete a logical router (mock)"""
        self.routers = [r for r in self.routers if r["name"] != name]
        logger.info(f"[MOCK] Deleted router: {name}")
        return True

    def delete_logical_router(self, name: str) -> bool:
        """Delete a logical router (mock) - alias"""
        return self.delete_router(name)

    def list_acls(self, switch: Optional[str] = None) -> List[Dict[str, Any]]:
        """List ACLs (mock)"""
        if switch:
            return [acl for acl in self.acls if acl.get("switch") == switch]
        return self.acls

    def create_acl(self, switch: str, direction: str, priority: int,
                    match: str, action: str) -> str:
        """Create an ACL rule (mock)"""
        acl_uuid = f"acl-{len(self.acls)}-uuid"
        acl = {
            "uuid": acl_uuid,
            "switch": switch,
            "direction": direction,
            "priority": priority,
            "match": match,
            "action": action
        }
        self.acls.append(acl)
        logger.info(f"[MOCK] Created ACL on {switch}")
        return acl_uuid

    def delete_acl(self, switch: str, direction: str, priority: int) -> bool:
        """Delete an ACL rule (mock)"""
        self.acls = [
            acl for acl in self.acls
            if not (acl["switch"] == switch and
                    acl["direction"] == direction and
                    acl["priority"] == priority)
        ]
        logger.info(f"[MOCK] Deleted ACL")
        return True

    def list_load_balancers(self) -> List[Dict[str, Any]]:
        """List load balancers (mock)"""
        return self.load_balancers

    def create_load_balancer(self, name: str, protocol: str,
                             vip: str, backends: List[str]) -> str:
        """Create a load balancer (mock)"""
        lb_uuid = f"lb-{len(self.load_balancers)}-uuid"
        lb = {
            "uuid": lb_uuid,
            "name": name,
            "protocol": protocol,
            "vip": vip,
            "backends": backends
        }
        self.load_balancers.append(lb)
        logger.info(f"[MOCK] Created load balancer: {name}")
        return lb_uuid

    def delete_load_balancer(self, name: str) -> bool:
        """Delete a load balancer (mock)"""
        self.load_balancers = [lb for lb in self.load_balancers if lb["name"] != name]
        logger.info(f"[MOCK] Deleted load balancer: {name}")
        return True
