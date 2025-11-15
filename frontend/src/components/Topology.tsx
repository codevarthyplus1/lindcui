import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { networksApi } from '../services/api';

export default function Topology() {
  const [topology, setTopology] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTopology();
  }, []);

  const loadTopology = async () => {
    setLoading(true);
    try {
      const response = await networksApi.getTopology();
      setTopology(response.data);
    } catch (error) {
      console.error('Failed to load topology:', error);
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

  if (!topology) {
    return (
      <Box>
        <Typography color="error">Failed to load network topology</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Network Topology</Typography>
        <IconButton onClick={loadTopology} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom color="primary">
              Logical Switches
            </Typography>
            {topology.switches && topology.switches.length > 0 ? (
              topology.switches.map((sw: any) => (
                <Card key={sw.uuid} sx={{ mb: 1 }}>
                  <CardContent>
                    <Typography variant="body1" fontWeight="bold">
                      {sw.name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      UUID: {sw.uuid}
                    </Typography>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Typography color="textSecondary">No logical switches</Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom color="secondary">
              Logical Routers
            </Typography>
            {topology.routers && topology.routers.length > 0 ? (
              topology.routers.map((router: any) => (
                <Card key={router.uuid} sx={{ mb: 1 }}>
                  <CardContent>
                    <Typography variant="body1" fontWeight="bold">
                      {router.name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      UUID: {router.uuid}
                    </Typography>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Typography color="textSecondary">No logical routers</Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom color="success.main">
              Load Balancers
            </Typography>
            {topology.load_balancers && topology.load_balancers.length > 0 ? (
              topology.load_balancers.map((lb: any) => (
                <Card key={lb.uuid} sx={{ mb: 1 }}>
                  <CardContent>
                    <Typography variant="body1" fontWeight="bold">
                      {lb.name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      UUID: {lb.uuid}
                    </Typography>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Typography color="textSecondary">No load balancers</Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Topology Visualization
            </Typography>
            <Box
              sx={{
                minHeight: 400,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '2px dashed #ccc',
                borderRadius: 2,
              }}
            >
              <Typography color="textSecondary">
                D3.js Network Diagram - Advanced visualization can be implemented here
              </Typography>
            </Box>
            <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
              Note: Full D3.js-based network topology visualization with nodes, edges, and interactive
              features can be implemented using react-d3-graph or custom D3.js components.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
