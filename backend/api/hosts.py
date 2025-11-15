"""
Host management API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from services.libvirt_manager import LibvirtManager
from config import settings

router = APIRouter()


class HostInfo(BaseModel):
    """Host information schema"""
    name: str
    address: str
    libvirt_uri: str
    enabled: bool


@router.get("")
async def list_hosts() -> List[Dict[str, Any]]:
    """List all configured hosts"""
    hosts = []

    for host_config in settings.hosts:
        host_data = {
            "name": host_config.name,
            "address": host_config.address,
            "libvirt_uri": host_config.libvirt_uri,
            "enabled": host_config.enabled,
            "status": "unknown"
        }

        # Try to get host status
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    host_info = libvirt_mgr.get_host_info()
                    host_data["status"] = "online"
                    host_data.update(host_info)
                else:
                    host_data["status"] = "offline"
        except Exception as e:
            host_data["status"] = "error"
            host_data["error"] = str(e)

        hosts.append(host_data)

    return hosts


@router.get("/{host_name}")
async def get_host(host_name: str) -> Dict[str, Any]:
    """Get detailed host information"""
    # Find host config
    host_config = None
    for hc in settings.hosts:
        if hc.name == host_name:
            host_config = hc
            break

    if not host_config:
        raise HTTPException(status_code=404, detail="Host not found")

    try:
        with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
            if not libvirt_mgr.conn:
                raise HTTPException(status_code=503, detail="Cannot connect to host")

            host_info = libvirt_mgr.get_host_info()
            vms = libvirt_mgr.list_vms()

            return {
                "name": host_config.name,
                "address": host_config.address,
                "status": "online",
                "info": host_info,
                "vms": vms,
                "vm_count": len(vms)
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{host_name}/vms")
async def list_host_vms(host_name: str) -> List[Dict[str, Any]]:
    """List all VMs on a specific host"""
    # Find host config
    host_config = None
    for hc in settings.hosts:
        if hc.name == host_name:
            host_config = hc
            break

    if not host_config:
        raise HTTPException(status_code=404, detail="Host not found")

    try:
        with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
            if not libvirt_mgr.conn:
                raise HTTPException(status_code=503, detail="Cannot connect to host")

            vms = libvirt_mgr.list_vms()
            return vms

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
