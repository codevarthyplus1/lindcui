"""
Cluster management service - orchestrates multiple hosts
"""
import logging
from typing import List, Dict, Any, Optional
from services.libvirt_manager import LibvirtManager
from services.ovn_manager import OVNManager
from services.ovs_manager import OVSManager
from config import settings

logger = logging.getLogger(__name__)


class ClusterManager:
    """Manager for cluster-wide operations"""

    def __init__(self):
        """Initialize cluster manager"""
        self.ovn_manager = OVNManager(settings.ovn.nb_db, settings.ovn.sb_db)
        self.ovs_manager = OVSManager()

    def get_cluster_status(self) -> Dict[str, Any]:
        """Get overall cluster status"""
        try:
            total_hosts = len(settings.hosts)
            online_hosts = 0
            total_vms = 0
            total_cpu_cores = 0
            total_memory = 0
            used_memory = 0

            for host_config in settings.hosts:
                try:
                    with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                        if libvirt_mgr.conn:
                            online_hosts += 1

                            # Get host info
                            host_info = libvirt_mgr.get_host_info()
                            total_cpu_cores += host_info.get("cpu_cores", 0)
                            total_memory += host_info.get("memory_total", 0)
                            used_memory += host_info.get("memory_used", 0)

                            # Get VMs
                            vms = libvirt_mgr.list_vms()
                            total_vms += len(vms)

                except Exception as e:
                    logger.error(f"Failed to get status for host {host_config.name}: {e}")
                    continue

            return {
                "cluster_name": settings.cluster.name,
                "total_hosts": total_hosts,
                "online_hosts": online_hosts,
                "offline_hosts": total_hosts - online_hosts,
                "total_vms": total_vms,
                "total_cpu_cores": total_cpu_cores,
                "total_memory_mb": total_memory,
                "used_memory_mb": used_memory,
                "free_memory_mb": total_memory - used_memory,
                "memory_usage_percent": (used_memory / total_memory * 100) if total_memory > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to get cluster status: {e}")
            raise

    def get_all_vms(self) -> List[Dict[str, Any]]:
        """Get all VMs across all hosts"""
        all_vms = []

        for host_config in settings.hosts:
            try:
                with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                    if libvirt_mgr.conn:
                        vms = libvirt_mgr.list_vms()

                        # Add host information to each VM
                        for vm in vms:
                            vm["host_name"] = host_config.name
                            vm["host_address"] = host_config.address

                        all_vms.extend(vms)

            except Exception as e:
                logger.error(f"Failed to get VMs from host {host_config.name}: {e}")
                continue

        return all_vms

    def find_best_host_for_vm(
        self,
        required_vcpus: int,
        required_memory: int
    ) -> Optional[str]:
        """Find the best host to place a new VM"""
        best_host = None
        max_free_memory = 0

        for host_config in settings.hosts:
            if not host_config.enabled:
                continue

            try:
                with LibvirtManager(host_config.libvirt_uri) as libvirt_mgr:
                    if not libvirt_mgr.conn:
                        continue

                    host_info = libvirt_mgr.get_host_info()

                    # Check if host has enough resources
                    if (host_info.get("cpu_cores", 0) >= required_vcpus and
                        host_info.get("memory_free", 0) >= required_memory):

                        # Select host with most free memory
                        free_memory = host_info.get("memory_free", 0)
                        if free_memory > max_free_memory:
                            max_free_memory = free_memory
                            best_host = host_config.libvirt_uri

            except Exception as e:
                logger.error(f"Failed to check host {host_config.name}: {e}")
                continue

        return best_host

    def get_network_topology(self) -> Dict[str, Any]:
        """Get complete network topology"""
        try:
            return self.ovn_manager.get_topology()
        except Exception as e:
            logger.error(f"Failed to get network topology: {e}")
            return {"switches": [], "routers": [], "load_balancers": []}

    def get_cluster_metrics(self) -> Dict[str, Any]:
        """Get cluster-wide metrics"""
        try:
            status = self.get_cluster_status()
            vms = self.get_all_vms()

            running_vms = len([vm for vm in vms if vm.get("status") == "running"])
            stopped_vms = len([vm for vm in vms if vm.get("status") == "stopped"])

            return {
                "cluster": status,
                "vms": {
                    "total": len(vms),
                    "running": running_vms,
                    "stopped": stopped_vms
                }
            }

        except Exception as e:
            logger.error(f"Failed to get cluster metrics: {e}")
            raise
