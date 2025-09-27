import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../App';
import { useToast } from '@/hooks/use-toast';
import Layout from '../components/Layout';
import { Users, FileText, UserPlus, TrendingUp, Building2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DistributorDashboard = () => {
  return (
    <Layout userRole="distributor">
      <Routes>
        <Route index element={<DistributorOverview />} />
        <Route path="retailers" element={<RetailerManagement />} />
        <Route path="certificates" element={<CertificateManagement />} />
        <Route path="*" element={<Navigate to="/distributor" replace />} />
      </Routes>
    </Layout>
  );
};

const DistributorOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch dashboard stats",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="distributor-overview">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Distributor Dashboard</h1>
        <p className="text-gray-600">Manage your retailer network and certificates</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="dashboard-card hover-lift">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">My Retailers</CardTitle>
            <Users className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{stats?.total_retailers || 0}</div>
            <p className="text-xs text-gray-600 mt-1">Retailers under you</p>
          </CardContent>
        </Card>

        <Card className="dashboard-card hover-lift">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Certificates</CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{stats?.total_certificates || 0}</div>
            <p className="text-xs text-gray-600 mt-1">From your retailers</p>
          </CardContent>
        </Card>

        <Card className="dashboard-card hover-lift">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Submitted</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{stats?.submitted_certificates || 0}</div>
            <p className="text-xs text-gray-600 mt-1">
              <span className="text-yellow-600 font-semibold">{stats?.draft_certificates || 0}</span> drafts
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="table-container">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-emerald-600" />
              Network Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">Active Retailers</p>
                  <p className="text-sm text-gray-600">Retailers with recent activity</p>
                </div>
                <Badge variant="secondary" className="bg-green-100 text-green-700">
                  {stats?.total_retailers || 0}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">Processing Rate</p>
                  <p className="text-sm text-gray-600">Certificate completion rate</p>
                </div>
                <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                  {stats?.total_certificates > 0 
                    ? Math.round((stats.submitted_certificates / stats.total_certificates) * 100)
                    : 0}%
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="table-container">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-600" />
              Certificate Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Certificates</span>
                <Badge variant="outline" className="text-blue-700 border-blue-300">
                  {stats?.total_certificates || 0}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Submitted</span>
                <Badge variant="outline" className="text-green-700 border-green-300">
                  {stats?.submitted_certificates || 0}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">In Progress</span>
                <Badge variant="outline" className="text-yellow-700 border-yellow-300">
                  {stats?.draft_certificates || 0}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const RetailerManagement = () => {
  const [retailers, setRetailers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateRetailer, setShowCreateRetailer] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchRetailers();
  }, []);

  const fetchRetailers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setRetailers(response.data.filter(user => user.role === 'retailer'));
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch retailers",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="retailer-management">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Retailer Management</h1>
          <p className="text-gray-600">Manage retailers under your distribution</p>
        </div>
        <Dialog open={showCreateRetailer} onOpenChange={setShowCreateRetailer}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="create-retailer-button">
              <UserPlus className="w-4 h-4 mr-2" />
              Add Retailer
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Retailer</DialogTitle>
            </DialogHeader>
            <CreateRetailerForm onSuccess={() => { setShowCreateRetailer(false); fetchRetailers(); }} />
          </DialogContent>
        </Dialog>
      </div>

      <Card className="table-container">
        <CardHeader>
          <CardTitle>My Retailers</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-500"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {retailers.map((retailer) => (
                  <TableRow key={retailer.id} data-testid={`retailer-row-${retailer.username}`}>
                    <TableCell className="font-medium">{retailer.username}</TableCell>
                    <TableCell>{retailer.company_name || '-'}</TableCell>
                    <TableCell>{retailer.contact_number || '-'}</TableCell>
                    <TableCell>{new Date(retailer.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="bg-green-100 text-green-700">
                        Active
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const CreateRetailerForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role: 'retailer',
    company_name: '',
    contact_number: ''
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/auth/register`, formData);
      toast({
        title: "Success",
        description: "Retailer added successfully",
      });
      onSuccess();
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to add retailer",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="username">Username</Label>
        <Input
          id="username"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          required
          data-testid="retailer-username-input"
        />
      </div>
      
      <div>
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          required
          data-testid="retailer-password-input"
        />
      </div>
      
      <div>
        <Label htmlFor="company_name">Company Name</Label>
        <Input
          id="company_name"
          value={formData.company_name}
          onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
          data-testid="retailer-company-input"
        />
      </div>
      
      <div>
        <Label htmlFor="contact_number">Contact Number</Label>
        <Input
          id="contact_number"
          value={formData.contact_number}
          onChange={(e) => setFormData({ ...formData, contact_number: e.target.value })}
          data-testid="retailer-contact-input"
        />
      </div>
      
      <Button type="submit" disabled={loading} className="w-full" data-testid="create-retailer-submit">
        {loading ? 'Adding...' : 'Add Retailer'}
      </Button>
    </form>
  );
};

const CertificateManagement = () => {
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchCertificates();
  }, []);

  const fetchCertificates = async () => {
    try {
      const response = await axios.get(`${API}/certificates`);
      setCertificates(response.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch certificates",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="distributor-certificates">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Certificate Management</h1>
        <p className="text-gray-600">Certificates from your retailers</p>
      </div>

      <Card className="table-container">
        <CardHeader>
          <CardTitle>Retailer Certificates</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-500"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Certificate No</TableHead>
                  <TableHead>Dealer</TableHead>
                  <TableHead>Vehicle</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {certificates.map((cert) => (
                  <TableRow key={cert.id} data-testid={`distributor-cert-row-${cert.certificate_no}`}>
                    <TableCell className="font-medium">{cert.certificate_no}</TableCell>
                    <TableCell>{cert.dealer_name}</TableCell>
                    <TableCell>{cert.vehicle_details.registration_no}</TableCell>
                    <TableCell>
                      <Badge 
                        variant="outline" 
                        className={cert.status === 'submitted' 
                          ? 'text-green-700 border-green-300' 
                          : 'text-yellow-700 border-yellow-300'
                        }
                      >
                        {cert.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{new Date(cert.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => window.open(`/certificate/${cert.id}`, '_blank')}
                        data-testid={`view-distributor-cert-${cert.id}`}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DistributorDashboard;