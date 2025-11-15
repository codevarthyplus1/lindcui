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
  IconButton,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { vmsApi } from '../services/api';

interface VM {
  uuid: string;
  name: string;
  status: string;
  vcpus: number;
  memory: number;
  host_name?: string;
  ip_addresses?: any[];
}

export default function VirtualMachines() {
  const [vms, setVMs] = useState<VM[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newVM, setNewVM] = useState({
    name: '',
    vcpus: 2,
    memory: 2048,
    disk_size: 20,
    network: 'default',
    os_variant: 'generic',
  });

  useEffect(() => {
    loadVMs();
  }, []);

  const loadVMs = async () => {
    setLoading(true);
    try {
      const response = await vmsApi.listVMs();
      setVMs(response.data);
    } catch (error) {
      console.error('Failed to load VMs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVM = async () => {
    try {
      await vmsApi.createVM(newVM);
      setCreateDialogOpen(false);
      setNewVM({
        name: '',
        vcpus: 2,
        memory: 2048,
        disk_size: 20,
        network: 'default',
        os_variant: 'generic',
      });
      loadVMs();
    } catch (error) {
      console.error('Failed to create VM:', error);
      alert('Failed to create VM');
    }
  };

  const handleStartVM = async (uuid: string) => {
    try {
      await vmsApi.startVM(uuid);
      setTimeout(loadVMs, 1000);
    } catch (error) {
      console.error('Failed to start VM:', error);
    }
  };

  const handleStopVM = async (uuid: string) => {
    try {
      await vmsApi.stopVM(uuid);
      setTimeout(loadVMs, 1000);
    } catch (error) {
      console.error('Failed to stop VM:', error);
    }
  };

  const handlePauseVM = async (uuid: string) => {
    try {
      await vmsApi.pauseVM(uuid);
      setTimeout(loadVMs, 1000);
    } catch (error) {
      console.error('Failed to pause VM:', error);
    }
  };

  const handleDeleteVM = async (uuid: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete VM "${name}"?`)) {
      try {
        await vmsApi.deleteVM(uuid);
        loadVMs();
      } catch (error) {
        console.error('Failed to delete VM:', error);
      }
    }
  };

  const getStatusChip = (status: string) => {
    const colors: any = {
      running: 'success',
      stopped: 'error',
      paused: 'warning',
      unknown: 'default',
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Virtual Machines</Typography>
        <Box>
          <IconButton onClick={loadVMs} color="primary">
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create VM
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Host</TableCell>
              <TableCell align="right">vCPUs</TableCell>
              <TableCell align="right">Memory (MB)</TableCell>
              <TableCell>IP Address</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {vms.map((vm) => (
              <TableRow key={vm.uuid} hover>
                <TableCell>
                  <Typography variant="body1" fontWeight="bold">
                    {vm.name}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {vm.uuid}
                  </Typography>
                </TableCell>
                <TableCell>{getStatusChip(vm.status)}</TableCell>
                <TableCell>{vm.host_name || '-'}</TableCell>
                <TableCell align="right">{vm.vcpus}</TableCell>
                <TableCell align="right">{vm.memory}</TableCell>
                <TableCell>
                  {vm.ip_addresses && vm.ip_addresses.length > 0
                    ? vm.ip_addresses[0].address
                    : '-'}
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Start">
                    <span>
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => handleStartVM(vm.uuid)}
                        disabled={vm.status === 'running'}
                      >
                        <StartIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Tooltip title="Stop">
                    <span>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleStopVM(vm.uuid)}
                        disabled={vm.status === 'stopped'}
                      >
                        <StopIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Tooltip title="Pause">
                    <span>
                      <IconButton
                        size="small"
                        color="warning"
                        onClick={() => handlePauseVM(vm.uuid)}
                        disabled={vm.status !== 'running'}
                      >
                        <PauseIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteVM(vm.uuid, vm.name)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {vms.length === 0 && (
        <Box mt={4} textAlign="center">
          <Typography color="textSecondary">No virtual machines found</Typography>
        </Box>
      )}

      {/* Create VM Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Virtual Machine</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Name"
              fullWidth
              value={newVM.name}
              onChange={(e) => setNewVM({ ...newVM, name: e.target.value })}
            />
            <TextField
              label="vCPUs"
              type="number"
              fullWidth
              value={newVM.vcpus}
              onChange={(e) => setNewVM({ ...newVM, vcpus: parseInt(e.target.value) })}
            />
            <TextField
              label="Memory (MB)"
              type="number"
              fullWidth
              value={newVM.memory}
              onChange={(e) => setNewVM({ ...newVM, memory: parseInt(e.target.value) })}
            />
            <TextField
              label="Disk Size (GB)"
              type="number"
              fullWidth
              value={newVM.disk_size}
              onChange={(e) => setNewVM({ ...newVM, disk_size: parseInt(e.target.value) })}
            />
            <TextField
              label="Network"
              fullWidth
              value={newVM.network}
              onChange={(e) => setNewVM({ ...newVM, network: e.target.value })}
            />
            <TextField
              label="OS Variant"
              fullWidth
              value={newVM.os_variant}
              onChange={(e) => setNewVM({ ...newVM, os_variant: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateVM} variant="contained" disabled={!newVM.name}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
