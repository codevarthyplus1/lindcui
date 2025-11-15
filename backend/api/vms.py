"""
Virtual Machine management API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services import LibvirtManager, ClusterManager
from config import settings

router = APIRouter()


class VMCreate(BaseModel):
    """VM creation schema"""
    name: str
    vcpus: int
    memory: int  # MB
    disk_size: int  # GB
    network: str = "default"
    os_variant: str = "generic"
    host_name: Optional[str] = None  # If not specified, auto-select


class VMAction(BaseModel):
    """VM action schema"""
    force: bool = False


@router.get("")
async def list_vms() -> List[Dict[str, Any]]:
    """List all VMs across all hosts"""
    try:
        cluster_mgr = ClusterManager()
        return cluster_mgr.get_all_vms()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_vm(vm_data: VMCreate) -> Dict[str, Any]:
    """Create a new VM"""
    try:
        # Determine target host
        if vm_data.host_name:
            # Use specified host
            host_config = None
            for hc in settings.hosts:
                if hc.name == vm_data.host_name:
                    host_config = hc
                    break

            if not host_config:
                raise HTTPException(status_code=404, detail="Host not found")

            libvirt_uri = host_config.libvirt_uri

        else:
            # Auto-select best host
            cluster_mgr = ClusterManager()
            libvirt_uri = cluster_mgr.find_best_host_for_vm(
                vm_data.vcpus,
                vm_data.memory
            )

            if not libvirt_uri:
                raise HTTPException(
                    status_code=503,
                    detail="No suitable host found with sufficient resources"
                )

        # Create VM
        with LibvirtManager(libvirt_uri) as libvirt_mgr:
            if not libvirt_mgr.conn:
                raise HTTPException(status_code=503, detail="Cannot connect to host")

            vm_uuid = libvirt_mgr.create_vm(
                name=vm_data.name,
                vcpus=vm_data.vcpus,
                memory=vm_data.memory,
                disk_size=vm_data.disk_size,
                network=vm_data.network,
                os_variant=vm_data.os_variant
            )

            return {
                "uuid": vm_uuid,
                "name": vm_data.name,
                "status": "created",
                "message": f"VM {vm_data.name} created successfully"
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vm_uuid}")
async def get_vm(vm_uuid: str) -> Dict[str, Any]:
    """Get VM details"""
    # Search for VM across all hosts
    for host_config in settings.hosts:
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    vm_info = libvirt_mgr.get_vm(vm_uuid)
                    if vm_info:
                        vm_info["host_name"] = host_config.name
                        vm_info["host_address"] = host_config.address
                        return vm_info

        except Exception:
            continue

    raise HTTPException(status_code=404, detail="VM not found")


@router.post("/{vm_uuid}/start")
async def start_vm(vm_uuid: str) -> Dict[str, Any]:
    """Start a VM"""
    # Find and start VM
    for host_config in settings.hosts:
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    vm_info = libvirt_mgr.get_vm(vm_uuid)
                    if vm_info:
                        libvirt_mgr.start_vm(vm_uuid)
                        return {
                            "uuid": vm_uuid,
                            "status": "running",
                            "message": f"VM started successfully"
                        }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="VM not found")


@router.post("/{vm_uuid}/stop")
async def stop_vm(vm_uuid: str, action: VMAction = VMAction()) -> Dict[str, Any]:
    """Stop a VM"""
    # Find and stop VM
    for host_config in settings.hosts:
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    vm_info = libvirt_mgr.get_vm(vm_uuid)
                    if vm_info:
                        libvirt_mgr.stop_vm(vm_uuid, force=action.force)
                        return {
                            "uuid": vm_uuid,
                            "status": "stopped",
                            "message": f"VM stopped successfully"
                        }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="VM not found")


@router.post("/{vm_uuid}/pause")
async def pause_vm(vm_uuid: str) -> Dict[str, Any]:
    """Pause a VM"""
    # Find and pause VM
    for host_config in settings.hosts:
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    vm_info = libvirt_mgr.get_vm(vm_uuid)
                    if vm_info:
                        libvirt_mgr.pause_vm(vm_uuid)
                        return {
                            "uuid": vm_uuid,
                            "status": "paused",
                            "message": f"VM paused successfully"
                        }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="VM not found")


@router.post("/{vm_uuid}/resume")
async def resume_vm(vm_uuid: str) -> Dict[str, Any]:
    """Resume a paused VM"""
    # Find and resume VM
    for host_config in settings.hosts:
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    vm_info = libvirt_mgr.get_vm(vm_uuid)
                    if vm_info:
                        libvirt_mgr.resume_vm(vm_uuid)
                        return {
                            "uuid": vm_uuid,
                            "status": "running",
                            "message": f"VM resumed successfully"
                        }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="VM not found")


@router.delete("/{vm_uuid}")
async def delete_vm(vm_uuid: str) -> Dict[str, Any]:
    """Delete a VM"""
    # Find and delete VM
    for host_config in settings.hosts:
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    vm_info = libvirt_mgr.get_vm(vm_uuid)
                    if vm_info:
                        libvirt_mgr.delete_vm(vm_uuid)
                        return {
                            "uuid": vm_uuid,
                            "status": "deleted",
                            "message": f"VM deleted successfully"
                        }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="VM not found")


@router.get("/{vm_uuid}/stats")
async def get_vm_stats(vm_uuid: str) -> Dict[str, Any]:
    """Get VM statistics"""
    # Find VM and get stats
    for host_config in settings.hosts:
        try:
            with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                if libvirt_mgr.conn:
                    vm_info = libvirt_mgr.get_vm(vm_uuid)
                    if vm_info:
                        stats = libvirt_mgr.get_vm_stats(vm_uuid)
                        return stats

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="VM not found")
