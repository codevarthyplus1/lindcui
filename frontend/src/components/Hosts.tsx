import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
} from '@mui/material';
import { hostsApi } from '../services/api';

interface Host {
  name: string;
  address: string;
  status: string;
  cpu_cores?: number;
  cpu_threads?: number;
  cpu_usage?: number;
  memory_total?: number;
  memory_used?: number;
  memory_free?: number;
  vm_count?: number;
}

export default function Hosts() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHosts();
    const interval = setInterval(loadHosts, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadHosts = async () => {
    try {
      const response = await hostsApi.listHosts();
      setHosts(response.data);
    } catch (error) {
      console.error('Failed to load hosts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    const colors: any = {
      online: 'success',
      offline: 'error',
      unknown: 'default',
      error: 'warning',
    };

    return <Chip label={status.toUpperCase()} color={colors[status] || 'default'} size="small" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        KVM Hosts
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Address</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">CPU Cores</TableCell>
              <TableCell align="right">CPU Usage</TableCell>
              <TableCell align="right">Memory (GB)</TableCell>
              <TableCell align="right">Memory Used</TableCell>
              <TableCell align="right">VMs</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {hosts.map((host) => (
              <TableRow key={host.name} hover>
                <TableCell>
                  <Typography variant="body1" fontWeight="bold">
                    {host.name}
                  </Typography>
                </TableCell>
                <TableCell>{host.address}</TableCell>
                <TableCell>{getStatusChip(host.status)}</TableCell>
                <TableCell align="right">
                  {host.cpu_cores ? `${host.cpu_cores} (${host.cpu_threads} threads)` : '-'}
                </TableCell>
                <TableCell align="right">
                  {host.cpu_usage !== undefined ? `${host.cpu_usage.toFixed(1)}%` : '-'}
                </TableCell>
                <TableCell align="right">
                  {host.memory_total ? (host.memory_total / 1024).toFixed(1) : '-'}
                </TableCell>
                <TableCell align="right">
                  {host.memory_used && host.memory_total
                    ? `${((host.memory_used / host.memory_total) * 100).toFixed(1)}%`
                    : '-'}
                </TableCell>
                <TableCell align="right">{host.vm_count || 0}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {hosts.length === 0 && (
        <Box mt={4} textAlign="center">
          <Typography color="textSecondary">No hosts configured</Typography>
        </Box>
      )}
    </Box>
  );
}
