"""
Business logic services
"""
import os

# Use mock services for testing if libvirt is not available
USE_MOCK = os.getenv("TEST_MODE", "0") == "1"

if USE_MOCK:
    from services.mock_libvirt_manager import LibvirtManager
    from services.mock_ovn_manager import OVNManager
    from services.mock_ovs_manager import OVSManager
else:
    try:
        from services.libvirt_manager import LibvirtManager
        from services.ovn_manager import OVNManager
        from services.ovs_manager import OVSManager
    except ImportError:
        # Fall back to mock if real services can't be imported
        from services.mock_libvirt_manager import LibvirtManager
        from services.mock_ovn_manager import OVNManager
        from services.mock_ovs_manager import OVSManager

from services.cluster_manager import ClusterManager

__all__ = [
    "LibvirtManager",
    "OVNManager",
    "OVSManager",
    "ClusterManager"
]
