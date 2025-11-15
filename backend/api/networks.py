"""
Network management API endpoints (OVN/OVS)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services import OVNManager, OVSManager
from config import settings

router = APIRouter()


# Pydantic models
class LogicalSwitchCreate(BaseModel):
    """Logical switch creation schema"""
    name: str
    subnet: str
    gateway: Optional[str] = None
    dns_servers: List[str] = ["8.8.8.8", "8.8.4.4"]
    enable_dhcp: bool = True
    dhcp_range_start: Optional[str] = None
    dhcp_range_end: Optional[str] = None


class LogicalRouterCreate(BaseModel):
    """Logical router creation schema"""
    name: str
    enable_snat: bool = True
    external_gateway: Optional[str] = None


class RouterSwitchConnect(BaseModel):
    """Router-Switch connection schema"""
    router_name: str
    switch_name: str
    ip_address: str


class ACLCreate(BaseModel):
    """ACL creation schema"""
    name: str
    entity_type: str  # "switch" or "port_group"
    entity_name: str
    direction: str  # "from-lport" or "to-lport"
    priority: int
    match: str
    action: str  # "allow", "allow-related", "drop", "reject"


class LoadBalancerCreate(BaseModel):
    """Load balancer creation schema"""
    name: str
    protocol: str  # "tcp", "udp", "sctp"
    vip: str  # "IP:port"
    backends: List[str]  # ["IP:port", ...]
    switches: List[str] = []  # Switches to attach to


# Initialize managers
def get_ovn_manager():
    return OVNManager(settings.ovn.nb_db, settings.ovn.sb_db)


def get_ovs_manager():
    return OVSManager()


# Logical Switch endpoints
@router.get("/switches")
async def list_switches() -> List[Dict[str, Any]]:
    """List all logical switches"""
    try:
        ovn_mgr = get_ovn_manager()
        return ovn_mgr.list_logical_switches()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switches")
async def create_switch(switch_data: LogicalSwitchCreate) -> Dict[str, Any]:
    """Create a logical switch"""
    try:
        ovn_mgr = get_ovn_manager()

        # Create switch
        switch_uuid = ovn_mgr.create_logical_switch(
            name=switch_data.name,
            subnet=switch_data.subnet
        )

        # Configure DHCP if enabled
        if switch_data.enable_dhcp and switch_data.gateway:
            ovn_mgr.configure_dhcp(
                switch_name=switch_data.name,
                subnet=switch_data.subnet,
                gateway=switch_data.gateway,
                dns_servers=switch_data.dns_servers,
                dhcp_range_start=switch_data.dhcp_range_start or "",
                dhcp_range_end=switch_data.dhcp_range_end or ""
            )

        return {
            "uuid": switch_uuid,
            "name": switch_data.name,
            "subnet": switch_data.subnet,
            "message": "Logical switch created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/switches/{switch_name}")
async def delete_switch(switch_name: str) -> Dict[str, Any]:
    """Delete a logical switch"""
    try:
        ovn_mgr = get_ovn_manager()
        ovn_mgr.delete_logical_switch(switch_name)

        return {
            "name": switch_name,
            "message": "Logical switch deleted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Logical Router endpoints
@router.get("/routers")
async def list_routers() -> List[Dict[str, Any]]:
    """List all logical routers"""
    try:
        ovn_mgr = get_ovn_manager()
        return ovn_mgr.list_logical_routers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routers")
async def create_router(router_data: LogicalRouterCreate) -> Dict[str, Any]:
    """Create a logical router"""
    try:
        ovn_mgr = get_ovn_manager()
        router_uuid = ovn_mgr.create_logical_router(router_data.name)

        return {
            "uuid": router_uuid,
            "name": router_data.name,
            "message": "Logical router created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/routers/{router_name}")
async def delete_router(router_name: str) -> Dict[str, Any]:
    """Delete a logical router"""
    try:
        ovn_mgr = get_ovn_manager()
        ovn_mgr.delete_logical_router(router_name)

        return {
            "name": router_name,
            "message": "Logical router deleted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect")
async def connect_router_switch(connection: RouterSwitchConnect) -> Dict[str, Any]:
    """Connect a logical switch to a router"""
    try:
        ovn_mgr = get_ovn_manager()
        ovn_mgr.connect_switch_to_router(
            switch_name=connection.switch_name,
            router_name=connection.router_name,
            ip_address=connection.ip_address
        )

        return {
            "switch": connection.switch_name,
            "router": connection.router_name,
            "message": "Switch connected to router successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ACL endpoints
@router.post("/acls")
async def create_acl(acl_data: ACLCreate) -> Dict[str, Any]:
    """Create an ACL rule"""
    try:
        ovn_mgr = get_ovn_manager()
        acl_uuid = ovn_mgr.create_acl(
            entity_type=acl_data.entity_type,
            entity_name=acl_data.entity_name,
            direction=acl_data.direction,
            priority=acl_data.priority,
            match=acl_data.match,
            action=acl_data.action
        )

        return {
            "uuid": acl_uuid,
            "name": acl_data.name,
            "message": "ACL created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Load Balancer endpoints
@router.get("/load-balancers")
async def list_load_balancers() -> List[Dict[str, Any]]:
    """List all load balancers"""
    try:
        ovn_mgr = get_ovn_manager()
        return ovn_mgr.list_load_balancers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-balancers")
async def create_load_balancer(lb_data: LoadBalancerCreate) -> Dict[str, Any]:
    """Create a load balancer"""
    try:
        ovn_mgr = get_ovn_manager()

        # Create load balancer
        lb_uuid = ovn_mgr.create_load_balancer(
            name=lb_data.name,
            protocol=lb_data.protocol,
            vip=lb_data.vip,
            backends=lb_data.backends
        )

        # Attach to switches
        for switch_name in lb_data.switches:
            ovn_mgr.add_load_balancer_to_switch(lb_data.name, switch_name)

        return {
            "uuid": lb_uuid,
            "name": lb_data.name,
            "vip": lb_data.vip,
            "message": "Load balancer created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/load-balancers/{lb_name}")
async def delete_load_balancer(lb_name: str) -> Dict[str, Any]:
    """Delete a load balancer"""
    try:
        ovn_mgr = get_ovn_manager()
        ovn_mgr.delete_load_balancer(lb_name)

        return {
            "name": lb_name,
            "message": "Load balancer deleted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# OVS Bridge endpoints
@router.get("/bridges")
async def list_bridges() -> List[str]:
    """List all OVS bridges"""
    try:
        ovs_mgr = get_ovs_manager()
        return ovs_mgr.list_bridges()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bridges/{bridge_name}")
async def get_bridge_info(bridge_name: str) -> Dict[str, Any]:
    """Get bridge information"""
    try:
        ovs_mgr = get_ovs_manager()
        return ovs_mgr.get_bridge_info(bridge_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topology")
async def get_topology() -> Dict[str, Any]:
    """Get complete network topology"""
    try:
        ovn_mgr = get_ovn_manager()
        return ovn_mgr.get_topology()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
