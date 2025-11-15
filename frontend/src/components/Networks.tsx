import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { networksApi } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Networks() {
  const [tabValue, setTabValue] = useState(0);
  const [switches, setSwitches] = useState<any[]>([]);
  const [routers, setRouters] = useState<any[]>([]);
  const [loadBalancers, setLoadBalancers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [switchDialog, setSwitchDialog] = useState(false);
  const [routerDialog, setRouterDialog] = useState(false);
  const [lbDialog, setLBDialog] = useState(false);

  const [newSwitch, setNewSwitch] = useState({
    name: '',
    subnet: '',
    gateway: '',
  });

  const [newRouter, setNewRouter] = useState({
    name: '',
  });

  const [newLB, setNewLB] = useState({
    name: '',
    protocol: 'tcp',
    vip: '',
    backends: '',
  });

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [switchesRes, routersRes, lbsRes] = await Promise.all([
        networksApi.listSwitches(),
        networksApi.listRouters(),
        networksApi.listLoadBalancers(),
      ]);

      setSwitches(switchesRes.data);
      setRouters(routersRes.data);
      setLoadBalancers(lbsRes.data);
    } catch (error) {
      console.error('Failed to load network data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSwitch = async () => {
    try {
      await networksApi.createSwitch(newSwitch);
      setSwitchDialog(false);
      setNewSwitch({ name: '', subnet: '', gateway: '' });
      loadAllData();
    } catch (error) {
      console.error('Failed to create switch:', error);
      alert('Failed to create switch');
    }
  };

  const handleCreateRouter = async () => {
    try {
      await networksApi.createRouter(newRouter);
      setRouterDialog(false);
      setNewRouter({ name: '' });
      loadAllData();
    } catch (error) {
      console.error('Failed to create router:', error);
      alert('Failed to create router');
    }
  };

  const handleCreateLB = async () => {
    try {
      const backends = newLB.backends.split(',').map((b) => b.trim());
      await networksApi.createLoadBalancer({
        name: newLB.name,
        protocol: newLB.protocol,
        vip: newLB.vip,
        backends,
        switches: [],
      });
      setLBDialog(false);
      setNewLB({ name: '', protocol: 'tcp', vip: '', backends: '' });
      loadAllData();
    } catch (error) {
      console.error('Failed to create load balancer:', error);
      alert('Failed to create load balancer');
    }
  };

  const handleDeleteSwitch = async (name: string) => {
    if (window.confirm(`Delete switch "${name}"?`)) {
      try {
        await networksApi.deleteSwitch(name);
        loadAllData();
      } catch (error) {
        console.error('Failed to delete switch:', error);
      }
    }
  };

  const handleDeleteRouter = async (name: string) => {
    if (window.confirm(`Delete router "${name}"?`)) {
      try {
        await networksApi.deleteRouter(name);
        loadAllData();
      } catch (error) {
        console.error('Failed to delete router:', error);
      }
    }
  };

  const handleDeleteLB = async (name: string) => {
    if (window.confirm(`Delete load balancer "${name}"?`)) {
      try {
        await networksApi.deleteLoadBalancer(name);
        loadAllData();
      } catch (error) {
        console.error('Failed to delete load balancer:', error);
      }
    }
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
        <Typography variant="h4">Network Management</Typography>
        <IconButton onClick={loadAllData} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      <Paper>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Logical Switches" />
          <Tab label="Logical Routers" />
          <Tab label="Load Balancers" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box mb={2}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setSwitchDialog(true)}>
              Create Switch
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>UUID</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {switches.map((sw) => (
                  <TableRow key={sw.uuid}>
                    <TableCell>{sw.name}</TableCell>
                    <TableCell>{sw.uuid}</TableCell>
                    <TableCell align="center">
                      <IconButton size="small" color="error" onClick={() => handleDeleteSwitch(sw.name)}>
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {switches.length === 0 && (
            <Box mt={2} textAlign="center">
              <Typography color="textSecondary">No logical switches</Typography>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box mb={2}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setRouterDialog(true)}>
              Create Router
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>UUID</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {routers.map((router) => (
                  <TableRow key={router.uuid}>
                    <TableCell>{router.name}</TableCell>
                    <TableCell>{router.uuid}</TableCell>
                    <TableCell align="center">
                      <IconButton size="small" color="error" onClick={() => handleDeleteRouter(router.name)}>
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {routers.length === 0 && (
            <Box mt={2} textAlign="center">
              <Typography color="textSecondary">No logical routers</Typography>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box mb={2}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setLBDialog(true)}>
              Create Load Balancer
            </Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>UUID</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loadBalancers.map((lb) => (
                  <TableRow key={lb.uuid}>
                    <TableCell>{lb.name}</TableCell>
                    <TableCell>{lb.uuid}</TableCell>
                    <TableCell align="center">
                      <IconButton size="small" color="error" onClick={() => handleDeleteLB(lb.name)}>
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {loadBalancers.length === 0 && (
            <Box mt={2} textAlign="center">
              <Typography color="textSecondary">No load balancers</Typography>
            </Box>
          )}
        </TabPanel>
      </Paper>

      {/* Create Switch Dialog */}
      <Dialog open={switchDialog} onClose={() => setSwitchDialog(false)}>
        <DialogTitle>Create Logical Switch</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1, minWidth: 400 }}>
            <TextField
              label="Name"
              fullWidth
              value={newSwitch.name}
              onChange={(e) => setNewSwitch({ ...newSwitch, name: e.target.value })}
            />
            <TextField
              label="Subnet (e.g., 10.0.1.0/24)"
              fullWidth
              value={newSwitch.subnet}
              onChange={(e) => setNewSwitch({ ...newSwitch, subnet: e.target.value })}
            />
            <TextField
              label="Gateway (e.g., 10.0.1.1)"
              fullWidth
              value={newSwitch.gateway}
              onChange={(e) => setNewSwitch({ ...newSwitch, gateway: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSwitchDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateSwitch} variant="contained" disabled={!newSwitch.name || !newSwitch.subnet}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Router Dialog */}
      <Dialog open={routerDialog} onClose={() => setRouterDialog(false)}>
        <DialogTitle>Create Logical Router</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1, minWidth: 400 }}>
            <TextField
              label="Name"
              fullWidth
              value={newRouter.name}
              onChange={(e) => setNewRouter({ ...newRouter, name: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRouterDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateRouter} variant="contained" disabled={!newRouter.name}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Load Balancer Dialog */}
      <Dialog open={lbDialog} onClose={() => setLBDialog(false)}>
        <DialogTitle>Create Load Balancer</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1, minWidth: 400 }}>
            <TextField
              label="Name"
              fullWidth
              value={newLB.name}
              onChange={(e) => setNewLB({ ...newLB, name: e.target.value })}
            />
            <TextField
              label="Protocol"
              select
              fullWidth
              value={newLB.protocol}
              onChange={(e) => setNewLB({ ...newLB, protocol: e.target.value })}
            >
              <option value="tcp">TCP</option>
              <option value="udp">UDP</option>
              <option value="sctp">SCTP</option>
            </TextField>
            <TextField
              label="VIP (e.g., 10.0.1.100:80)"
              fullWidth
              value={newLB.vip}
              onChange={(e) => setNewLB({ ...newLB, vip: e.target.value })}
            />
            <TextField
              label="Backends (comma-separated, e.g., 10.0.1.10:80,10.0.1.11:80)"
              fullWidth
              multiline
              rows={2}
              value={newLB.backends}
              onChange={(e) => setNewLB({ ...newLB, backends: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLBDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateLB}
            variant="contained"
            disabled={!newLB.name || !newLB.vip || !newLB.backends}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
