"""
Mock libvirt manager for testing without actual libvirt installation
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class LibvirtManager:
    """Mock manager for libvirt operations - for testing"""

    def __init__(self, libvirt_uri: str):
        """Initialize mock libvirt connection"""
        self.libvirt_uri = libvirt_uri
        self.conn: bool = False
        self.mock_vms = []

    def connect(self) -> bool:
        """Mock connect to libvirt"""
        logger.info(f"[MOCK] Connected to libvirt: {self.libvirt_uri}")
        self.conn = True
        return True

    def disconnect(self):
        """Mock disconnect from libvirt"""
        self.conn = False

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def get_host_info(self) -> Dict[str, Any]:
        """Get mock host information"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        # Return mock data
        return {
            "hostname": f"test-host-{random.randint(1, 3)}",
            "libvirt_version": 9010000,
            "cpu_model": "x86_64",
            "cpu_cores": 8,
            "cpu_threads": 16,
            "cpu_mhz": 2400,
            "memory_total": 32768,  # MB
            "memory_free": 16384,
            "memory_used": 16384,
            "cpu_usage": random.uniform(10.0, 50.0),
            "numa_nodes": 1
        }

    def list_vms(self) -> List[Dict[str, Any]]:
        """List all VMs on the host (mock)"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        return self.mock_vms

    def get_vm_info(self, vm_name: str) -> Optional[Dict[str, Any]]:
        """Get VM information (mock)"""
        for vm in self.mock_vms:
            if vm["name"] == vm_name:
                return vm
        return None

    def create_vm(self, name: str, vcpus: int = 2, memory: int = 2048,
                   disk_size: int = 20, network: str = "default",
                   os_variant: str = "ubuntu22.04", **kwargs) -> str:
        """Create a new VM (mock)"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        vm_uuid = f"mock-uuid-{random.randint(1000, 9999)}"
        vm = {
            "name": name,
            "uuid": vm_uuid,
            "state": "shutoff",
            "vcpus": vcpus,
            "memory": memory,
            "disk_size": disk_size,
            "network": network,
            "os_variant": os_variant,
            "created_at": datetime.utcnow().isoformat()
        }
        self.mock_vms.append(vm)
        logger.info(f"[MOCK] Created VM: {vm['name']}")
        return vm_uuid

    def start_vm(self, vm_name: str) -> bool:
        """Start a VM (mock)"""
        vm = self.get_vm_info(vm_name)
        if vm:
            vm["state"] = "running"
            logger.info(f"[MOCK] Started VM: {vm_name}")
            return True
        return False

    def stop_vm(self, vm_name: str) -> bool:
        """Stop a VM (mock)"""
        vm = self.get_vm_info(vm_name)
        if vm:
            vm["state"] = "shutoff"
            logger.info(f"[MOCK] Stopped VM: {vm_name}")
            return True
        return False

    def pause_vm(self, vm_name: str) -> bool:
        """Pause a VM (mock)"""
        vm = self.get_vm_info(vm_name)
        if vm:
            vm["state"] = "paused"
            logger.info(f"[MOCK] Paused VM: {vm_name}")
            return True
        return False

    def resume_vm(self, vm_name: str) -> bool:
        """Resume a VM (mock)"""
        vm = self.get_vm_info(vm_name)
        if vm:
            vm["state"] = "running"
            logger.info(f"[MOCK] Resumed VM: {vm_name}")
            return True
        return False

    def delete_vm(self, vm_name: str) -> bool:
        """Delete a VM (mock)"""
        self.mock_vms = [vm for vm in self.mock_vms if vm["name"] != vm_name]
        logger.info(f"[MOCK] Deleted VM: {vm_name}")
        return True

    def get_vm_stats(self, vm_name: str) -> Optional[Dict[str, Any]]:
        """Get VM statistics (mock)"""
        vm = self.get_vm_info(vm_name)
        if vm:
            return {
                "cpu_time": random.randint(100000000, 999999999),
                "cpu_usage": random.uniform(0.0, 100.0),
                "memory_used": int(vm["memory"] * random.uniform(0.3, 0.9)),
                "memory_total": vm["memory"],
                "network_rx": random.randint(1000000, 999999999),
                "network_tx": random.randint(1000000, 999999999),
            }
        return None
