"""
Cluster management API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.cluster_manager import ClusterManager

router = APIRouter()


@router.get("/status")
async def get_cluster_status() -> Dict[str, Any]:
    """Get cluster status"""
    try:
        cluster_mgr = ClusterManager()
        return cluster_mgr.get_cluster_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_cluster_metrics() -> Dict[str, Any]:
    """Get cluster metrics"""
    try:
        cluster_mgr = ClusterManager()
        return cluster_mgr.get_cluster_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topology")
async def get_network_topology() -> Dict[str, Any]:
    """Get network topology"""
    try:
        cluster_mgr = ClusterManager()
        return cluster_mgr.get_network_topology()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
