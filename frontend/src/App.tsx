import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Hosts from './components/Hosts';
import VirtualMachines from './components/VirtualMachines';
import Networks from './components/Networks';
import Topology from './components/Topology';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/hosts" element={<Hosts />} />
            <Route path="/vms" element={<VirtualMachines />} />
            <Route path="/networks" element={<Networks />} />
            <Route path="/topology" element={<Topology />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
