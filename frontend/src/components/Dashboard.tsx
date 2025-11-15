import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  Computer as HostIcon,
  Dns as VmIcon,
  CheckCircle as OnlineIcon,
  Error as OfflineIcon,
} from '@mui/icons-material';
import { clusterApi, vmsApi } from '../services/api';

interface ClusterMetrics {
  cluster: {
    cluster_name: string;
    total_hosts: number;
    online_hosts: number;
    offline_hosts: number;
    total_vms: number;
    total_cpu_cores: number;
    total_memory_mb: number;
    used_memory_mb: number;
    free_memory_mb: number;
    memory_usage_percent: number;
  };
  vms: {
    total: number;
    running: number;
    stopped: number;
  };
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<ClusterMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    try {
      const response = await clusterApi.getMetrics();
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!metrics) {
    return (
      <Box>
        <Typography color="error">Failed to load cluster metrics</Typography>
      </Box>
    );
  }

  const StatCard = ({ title, value, icon, color }: any) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4">{value}</Typography>
          </Box>
          <Box sx={{ color, fontSize: 48 }}>{icon}</Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard - {metrics.cluster.cluster_name}
      </Typography>

      <Grid container spacing={3}>
        {/* Cluster Stats */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Hosts"
            value={metrics.cluster.total_hosts}
            icon={<HostIcon fontSize="inherit" />}
            color="primary.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Online Hosts"
            value={metrics.cluster.online_hosts}
            icon={<OnlineIcon fontSize="inherit" />}
            color="success.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total VMs"
            value={metrics.vms.total}
            icon={<VmIcon fontSize="inherit" />}
            color="info.main"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Running VMs"
            value={metrics.vms.running}
            icon={<OnlineIcon fontSize="inherit" />}
            color="success.main"
          />
        </Grid>

        {/* Resource Overview */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              CPU Resources
            </Typography>
            <Typography variant="h3" color="primary">
              {metrics.cluster.total_cpu_cores}
            </Typography>
            <Typography color="textSecondary">Total CPU Cores</Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Memory Resources
            </Typography>
            <Typography variant="h3" color="primary">
              {(metrics.cluster.total_memory_mb / 1024).toFixed(1)} GB
            </Typography>
            <Typography color="textSecondary">
              Used: {(metrics.cluster.used_memory_mb / 1024).toFixed(1)} GB (
              {metrics.cluster.memory_usage_percent.toFixed(1)}%)
            </Typography>
            <Typography color="textSecondary">
              Free: {(metrics.cluster.free_memory_mb / 1024).toFixed(1)} GB
            </Typography>
          </Paper>
        </Grid>

        {/* VM Status */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Virtual Machine Status
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center" p={2}>
                  <Typography variant="h4" color="info.main">
                    {metrics.vms.total}
                  </Typography>
                  <Typography color="textSecondary">Total VMs</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center" p={2}>
                  <Typography variant="h4" color="success.main">
                    {metrics.vms.running}
                  </Typography>
                  <Typography color="textSecondary">Running</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center" p={2}>
                  <Typography variant="h4" color="error.main">
                    {metrics.vms.stopped}
                  </Typography>
                  <Typography color="textSecondary">Stopped</Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
