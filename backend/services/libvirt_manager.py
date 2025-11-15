"""
Libvirt management service for KVM/QEMU operations
"""
import logging
import libvirt
import uuid as uuid_lib
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LibvirtManager:
    """Manager for libvirt operations on KVM hosts"""

    def __init__(self, libvirt_uri: str):
        """Initialize libvirt connection"""
        self.libvirt_uri = libvirt_uri
        self.conn: Optional[libvirt.virConnect] = None

    def connect(self) -> bool:
        """Connect to libvirt"""
        try:
            self.conn = libvirt.open(self.libvirt_uri)
            logger.info(f"Connected to libvirt: {self.libvirt_uri}")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to connect to libvirt: {e}")
            return False

    def disconnect(self):
        """Disconnect from libvirt"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def get_host_info(self) -> Dict[str, Any]:
        """Get host information"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            info = self.conn.getInfo()
            hostname = self.conn.getHostname()
            version = self.conn.getVersion()

            # Get node info
            node_info = {
                "hostname": hostname,
                "libvirt_version": version,
                "cpu_model": info[0],
                "cpu_cores": info[2],
                "cpu_threads": info[6],
                "cpu_mhz": info[3],
                "memory_total": info[1],  # MB
                "numa_nodes": info[4]
            }

            # Get memory stats
            mem_stats = self.conn.getMemoryStats(libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS, 0)
            if mem_stats:
                node_info["memory_free"] = mem_stats.get("free", 0) // 1024  # KB to MB
                node_info["memory_used"] = (node_info["memory_total"] - node_info["memory_free"])

            # Get CPU stats
            cpu_stats = self.conn.getCPUStats(libvirt.VIR_NODE_CPU_STATS_ALL_CPUS, 0)
            if cpu_stats:
                # Calculate CPU usage percentage (simplified)
                total = sum(cpu_stats.values())
                idle = cpu_stats.get("idle", 0)
                if total > 0:
                    node_info["cpu_usage"] = ((total - idle) / total) * 100
                else:
                    node_info["cpu_usage"] = 0.0

            return node_info

        except libvirt.libvirtError as e:
            logger.error(f"Failed to get host info: {e}")
            raise

    def list_vms(self) -> List[Dict[str, Any]]:
        """List all VMs on the host"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        vms = []
        try:
            # Get all domains (both active and inactive)
            for domain in self.conn.listAllDomains(0):
                vm_info = self._get_vm_info(domain)
                vms.append(vm_info)

            return vms

        except libvirt.libvirtError as e:
            logger.error(f"Failed to list VMs: {e}")
            raise

    def _get_vm_info(self, domain: libvirt.virDomain) -> Dict[str, Any]:
        """Get VM information from domain"""
        try:
            state, max_mem, memory, vcpus, cpu_time = domain.info()

            # Map state to string
            state_map = {
                libvirt.VIR_DOMAIN_NOSTATE: "nostate",
                libvirt.VIR_DOMAIN_RUNNING: "running",
                libvirt.VIR_DOMAIN_BLOCKED: "blocked",
                libvirt.VIR_DOMAIN_PAUSED: "paused",
                libvirt.VIR_DOMAIN_SHUTDOWN: "shutdown",
                libvirt.VIR_DOMAIN_SHUTOFF: "stopped",
                libvirt.VIR_DOMAIN_CRASHED: "crashed",
                libvirt.VIR_DOMAIN_PMSUSPENDED: "suspended"
            }

            vm_info = {
                "uuid": domain.UUIDString(),
                "name": domain.name(),
                "status": state_map.get(state, "unknown"),
                "vcpus": vcpus,
                "memory": memory // 1024,  # KB to MB
                "max_memory": max_mem // 1024,  # KB to MB
                "cpu_time": cpu_time,
                "autostart": domain.autostart() == 1
            }

            # Get network interfaces
            try:
                interfaces = domain.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
                vm_info["interfaces"] = []
                vm_info["ip_addresses"] = []

                for iface_name, iface_data in interfaces.items():
                    vm_info["interfaces"].append({
                        "name": iface_name,
                        "mac": iface_data["hwaddr"]
                    })

                    if iface_data["addrs"]:
                        for addr in iface_data["addrs"]:
                            vm_info["ip_addresses"].append({
                                "address": addr["addr"],
                                "type": "ipv4" if addr["type"] == libvirt.VIR_IP_ADDR_TYPE_IPV4 else "ipv6"
                            })
            except Exception as e:
                logger.debug(f"Failed to get network interfaces for {domain.name()}: {e}")
                vm_info["interfaces"] = []
                vm_info["ip_addresses"] = []

            return vm_info

        except libvirt.libvirtError as e:
            logger.error(f"Failed to get VM info: {e}")
            raise

    def get_vm(self, vm_uuid: str) -> Optional[Dict[str, Any]]:
        """Get VM by UUID"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            domain = self.conn.lookupByUUIDString(vm_uuid)
            return self._get_vm_info(domain)
        except libvirt.libvirtError:
            return None

    def create_vm(
        self,
        name: str,
        vcpus: int,
        memory: int,  # MB
        disk_size: int,  # GB
        network: str = "default",
        os_variant: str = "generic"
    ) -> str:
        """Create a new VM"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        vm_uuid = str(uuid_lib.uuid4())

        # Simple XML template for VM creation
        xml = f"""
        <domain type='kvm'>
          <name>{name}</name>
          <uuid>{vm_uuid}</uuid>
          <memory unit='MiB'>{memory}</memory>
          <vcpu>{vcpus}</vcpu>
          <os>
            <type arch='x86_64'>hvm</type>
            <boot dev='hd'/>
          </os>
          <features>
            <acpi/>
            <apic/>
          </features>
          <devices>
            <disk type='file' device='disk'>
              <driver name='qemu' type='qcow2'/>
              <source file='/var/lib/libvirt/images/{name}.qcow2'/>
              <target dev='vda' bus='virtio'/>
            </disk>
            <interface type='network'>
              <source network='{network}'/>
              <model type='virtio'/>
            </interface>
            <console type='pty'>
              <target type='serial' port='0'/>
            </console>
            <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'/>
          </devices>
        </domain>
        """

        try:
            # Create disk image (simplified - should use proper storage pool management)
            logger.info(f"Creating VM {name} with UUID {vm_uuid}")

            # Define the domain
            domain = self.conn.defineXML(xml)
            logger.info(f"VM {name} created successfully")

            return vm_uuid

        except libvirt.libvirtError as e:
            logger.error(f"Failed to create VM: {e}")
            raise

    def start_vm(self, vm_uuid: str) -> bool:
        """Start a VM"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            domain = self.conn.lookupByUUIDString(vm_uuid)
            domain.create()
            logger.info(f"VM {vm_uuid} started")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to start VM: {e}")
            raise

    def stop_vm(self, vm_uuid: str, force: bool = False) -> bool:
        """Stop a VM"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            domain = self.conn.lookupByUUIDString(vm_uuid)

            if force:
                domain.destroy()  # Force stop
            else:
                domain.shutdown()  # Graceful shutdown

            logger.info(f"VM {vm_uuid} stopped (force={force})")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to stop VM: {e}")
            raise

    def pause_vm(self, vm_uuid: str) -> bool:
        """Pause a VM"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            domain = self.conn.lookupByUUIDString(vm_uuid)
            domain.suspend()
            logger.info(f"VM {vm_uuid} paused")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to pause VM: {e}")
            raise

    def resume_vm(self, vm_uuid: str) -> bool:
        """Resume a paused VM"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            domain = self.conn.lookupByUUIDString(vm_uuid)
            domain.resume()
            logger.info(f"VM {vm_uuid} resumed")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to resume VM: {e}")
            raise

    def delete_vm(self, vm_uuid: str) -> bool:
        """Delete a VM"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            domain = self.conn.lookupByUUIDString(vm_uuid)

            # Stop if running
            if domain.isActive():
                domain.destroy()

            # Undefine (delete)
            domain.undefine()
            logger.info(f"VM {vm_uuid} deleted")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to delete VM: {e}")
            raise

    def get_vm_stats(self, vm_uuid: str) -> Dict[str, Any]:
        """Get VM statistics"""
        if not self.conn:
            raise Exception("Not connected to libvirt")

        try:
            domain = self.conn.lookupByUUIDString(vm_uuid)

            if not domain.isActive():
                return {"cpu_usage": 0.0, "memory_usage": 0.0}

            # Get CPU stats
            cpu_stats = domain.getCPUStats(True)

            # Get memory stats
            mem_stats = domain.memoryStats()

            return {
                "cpu_usage": 0.0,  # Simplified - proper calculation needed
                "memory_usage": mem_stats.get("actual", 0) / 1024 if mem_stats else 0.0
            }

        except libvirt.libvirtError as e:
            logger.error(f"Failed to get VM stats: {e}")
            return {"cpu_usage": 0.0, "memory_usage": 0.0}
