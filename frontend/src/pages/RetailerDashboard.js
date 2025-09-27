import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../App';
import { useToast } from '@/hooks/use-toast';
import Layout from '../components/Layout';
import { FileText, PlusCircle, TrendingUp, Clock, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RetailerDashboard = () => {
  return (
    <Layout userRole="retailer">
      <Routes>
        <Route index element={<RetailerOverview />} />
        <Route path="certificates" element={<CertificateManagement />} />
        <Route path="*" element={<Navigate to="/retailer" replace />} />
      </Routes>
    </Layout>
  );
};

const RetailerOverview = () => {
  const [stats, setStats] = useState(null);
  const [recentCertificates, setRecentCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchStats();
    fetchRecentCertificates();
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
    }
  };

  const fetchRecentCertificates = async () => {
    try {
      const response = await axios.get(`${API}/certificates`);
      // Get the 5 most recent certificates
      const recent = response.data
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);
      setRecentCertificates(recent);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch recent certificates",
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
    <div className="space-y-6" data-testid="retailer-overview">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Retailer Dashboard</h1>
          <p className="text-gray-600">Manage your vehicle conspicuity certificates</p>
        </div>
        <Link to="/certificate/new">
          <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="new-certificate-button">
            <PlusCircle className="w-4 h-4 mr-2" />
            New Certificate
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="dashboard-card hover-lift">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Certificates</CardTitle>
            <FileText className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{stats?.total_certificates || 0}</div>
            <p className="text-xs text-gray-600 mt-1">All time certificates</p>
          </CardContent>
        </Card>

        <Card className="dashboard-card hover-lift">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Submitted</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{stats?.submitted_certificates || 0}</div>
            <p className="text-xs text-gray-600 mt-1">Completed certificates</p>
          </CardContent>
        </Card>

        <Card className="dashboard-card hover-lift">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Drafts</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{stats?.draft_certificates || 0}</div>
            <p className="text-xs text-gray-600 mt-1">In progress</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="table-container">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-600" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Link to="/certificate/new">
                <Button className="w-full justify-start gap-3 h-12 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200" data-testid="quick-new-certificate">
                  <PlusCircle className="w-5 h-5" />
                  Create New Certificate
                </Button>
              </Link>
              
              <Link to="/retailer/certificates">
                <Button variant="outline" className="w-full justify-start gap-3 h-12" data-testid="quick-view-certificates">
                  <FileText className="w-5 h-5" />
                  View All Certificates
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card className="table-container">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-600" />
              Recent Certificates
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentCertificates.length > 0 ? (
              <div className="space-y-3">
                {recentCertificates.map((cert) => (
                  <div key={cert.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg" data-testid={`recent-cert-${cert.certificate_no}`}>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 text-sm">{cert.certificate_no}</p>
                      <p className="text-xs text-gray-600">{cert.vehicle_details.registration_no}</p>
                    </div>
                    <div className="text-right">
                      <Badge 
                        variant="outline" 
                        className={cert.status === 'submitted' 
                          ? 'text-green-700 border-green-300' 
                          : 'text-yellow-700 border-yellow-300'
                        }
                      >
                        {cert.status}
                      </Badge>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(cert.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 mb-4">No certificates yet</p>
                <Link to="/certificate/new">
                  <Button size="sm" data-testid="create-first-certificate">
                    Create Your First Certificate
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
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
    <div className="space-y-6" data-testid="retailer-certificates">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Certificates</h1>
          <p className="text-gray-600">Manage your vehicle conspicuity certificates</p>
        </div>
        <Link to="/certificate/new">
          <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="new-certificate-from-list">
            <PlusCircle className="w-4 h-4 mr-2" />
            New Certificate
          </Button>
        </Link>
      </div>

      <Card className="table-container">
        <CardHeader>
          <CardTitle>All Certificates</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-500"></div>
            </div>
          ) : certificates.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Certificate No</TableHead>
                  <TableHead>Vehicle Registration</TableHead>
                  <TableHead>Dealer License</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {certificates.map((cert) => (
                  <TableRow key={cert.id} data-testid={`retailer-cert-row-${cert.certificate_no}`}>
                    <TableCell className="font-medium">{cert.certificate_no}</TableCell>
                    <TableCell>{cert.vehicle_details.registration_no}</TableCell>
                    <TableCell>{cert.dealer_license}</TableCell>
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
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => window.open(`/certificate/${cert.id}`, '_blank')}
                          data-testid={`view-cert-${cert.id}`}
                        >
                          View
                        </Button>
                        {cert.status === 'draft' && (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => window.open(`/certificate/edit/${cert.id}`, '_blank')}
                            data-testid={`edit-cert-${cert.id}`}
                          >
                            Edit
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No certificates found</h3>
              <p className="text-gray-500 mb-6">You haven't created any certificates yet. Start by creating your first certificate.</p>
              <Link to="/certificate/new">
                <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="no-certs-create-new">
                  <PlusCircle className="w-4 h-4 mr-2" />
                  Create Certificate
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default RetailerDashboard;