import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../App';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Download, Edit, Building2, Car, User, FileText, Calendar } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CertificateView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [certificate, setCertificate] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchCertificate();
  }, [id]);

  const fetchCertificate = async () => {
    try {
      const response = await axios.get(`${API}/certificates/${id}`);
      setCertificate(response.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch certificate",
        variant: "destructive",
      });
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const goBack = () => {
    switch (user.role) {
      case 'admin':
        navigate('/admin/certificates');
        break;
      case 'distributor':
        navigate('/distributor/certificates');
        break;
      case 'retailer':
        navigate('/retailer/certificates');
        break;
      default:
        navigate(-1);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (!certificate) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Certificate Not Found</h1>
          <Button onClick={goBack}>Go Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6 print:hidden">
          <div className="flex items-center gap-4">
            <Button 
              variant="outline" 
              onClick={goBack}
              className="flex items-center gap-2"
              data-testid="back-button"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Certificate Details</h1>
              <p className="text-gray-600">Vehicle Conspicuity Certificate</p>
            </div>
          </div>
          
          <div className="flex gap-2">
            {user.role === 'retailer' && certificate.status === 'draft' && (
              <Button 
                variant="outline"
                onClick={() => navigate(`/certificate/edit/${certificate.id}`)}
                className="flex items-center gap-2"
                data-testid="edit-certificate-button"
              >
                <Edit className="w-4 h-4" />
                Edit
              </Button>
            )}
            <Button 
              onClick={handlePrint}
              className="bg-emerald-600 hover:bg-emerald-700 flex items-center gap-2"
              data-testid="print-certificate-button"
            >
              <Download className="w-4 h-4" />
              Print
            </Button>
          </div>
        </div>

        {/* Certificate Content */}
        <div className="certificate-container" data-testid="certificate-content">
          {/* Header */}
          <div className="certificate-header">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center">
                  <Building2 className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Vehicle Conspicuity</h1>
                  <p className="text-lg text-gray-600">Online MIS Certificate</p>
                  <p className="text-sm text-gray-500">Compliance to Automotive Industry Standard - 089, 090 & 037</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600 mb-1">Certificate No:</div>
                <div className="text-lg font-bold text-gray-900">{certificate.certificate_no}</div>
                <div className="text-sm text-gray-600 mt-2">Fitment Date:</div>
                <div className="text-sm text-gray-700">{new Date(certificate.fitment_date).toLocaleDateString()}</div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <Badge 
                variant="outline" 
                className={certificate.status === 'submitted' 
                  ? 'text-green-700 border-green-300 bg-green-50' 
                  : 'text-yellow-700 border-yellow-300 bg-yellow-50'
                }
              >
                {certificate.status.toUpperCase()}
              </Badge>
              <div className="text-sm text-gray-600">
                Created: {new Date(certificate.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          {/* Vehicle Details */}
          <div className="certificate-section">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Car className="w-5 h-5 text-emerald-600" />
              Vehicle Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="certificate-field">
                <span className="field-label">Registration No:</span>
                <span className="field-value font-semibold">{certificate.vehicle_details.registration_no}</span>
              </div>
              <div className="certificate-field">
                <span className="field-label">Chassis No:</span>
                <span className="field-value">{certificate.vehicle_details.chassis_no}</span>
              </div>
              <div className="certificate-field">
                <span className="field-label">Vehicle Make:</span>
                <span className="field-value">{certificate.vehicle_details.vehicle_make}</span>
              </div>
              <div className="certificate-field">
                <span className="field-label">Vehicle Model:</span>
                <span className="field-value">{certificate.vehicle_details.vehicle_model}</span>
              </div>
              <div className="certificate-field">
                <span className="field-label">Registration Year:</span>
                <span className="field-value">{certificate.vehicle_details.registration_year}</span>
              </div>
              <div className="certificate-field">
                <span className="field-label">Engine No:</span>
                <span className="field-value">{certificate.vehicle_details.engine_no}</span>
              </div>
            </div>
          </div>

          {/* Owner Details */}
          <div className="certificate-section">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-emerald-600" />
              Owner Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="certificate-field">
                <span className="field-label">Owner Name:</span>
                <span className="field-value font-semibold">{certificate.owner_details.owner_name}</span>
              </div>
              <div className="certificate-field">
                <span className="field-label">Contact Number:</span>
                <span className="field-value">{certificate.owner_details.contact_number}</span>
              </div>
            </div>
          </div>

          {/* Dealer Details */}
          <div className="certificate-section">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-600" />
              Dealer/Applicator Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="certificate-field">
                <span className="field-label">Dealer Name:</span>
                <span className="field-value font-semibold">{certificate.dealer_name}</span>
              </div>
              <div className="certificate-field">
                <span className="field-label">License Number:</span>
                <span className="field-value">{certificate.dealer_license}</span>
              </div>
            </div>
          </div>

          {/* Fitment Details */}
          <div className="certificate-section">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              Conspicuity Tapes & Fitment Details
            </h3>
            
            {/* 20MM Tapes */}
            <div className="mb-6">
              <h4 className="font-semibold text-gray-800 mb-3">Conspicuity Tapes 20MM</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="certificate-field">
                  <span className="field-label">Red 20MM:</span>
                  <span className="field-value">{certificate.fitment_details.red_20mm}m</span>
                </div>
                <div className="certificate-field">
                  <span className="field-label">White 20MM:</span>
                  <span className="field-value">{certificate.fitment_details.white_20mm}m</span>
                </div>
                <div className="certificate-field">
                  <span className="field-label">Yellow 20MM:</span>
                  <span className="field-value">{certificate.fitment_details.yellow_20mm}m</span>
                </div>
              </div>
            </div>

            {/* 50MM Tapes */}
            <div className="mb-6">
              <h4 className="font-semibold text-gray-800 mb-3">Conspicuity Tapes 50MM</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="certificate-field">
                  <span className="field-label">Red 50MM:</span>
                  <span className="field-value">{certificate.fitment_details.red_50mm}m</span>
                </div>
                <div className="certificate-field">
                  <span className="field-label">White 50MM:</span>
                  <span className="field-value">{certificate.fitment_details.white_50mm}m</span>
                </div>
                <div className="certificate-field">
                  <span className="field-label">Yellow 50MM:</span>
                  <span className="field-value">{certificate.fitment_details.yellow_50mm}m</span>
                </div>
              </div>
            </div>

            {/* Marketing Plates */}
            <div>
              <h4 className="font-semibold text-gray-800 mb-3">Rear Marketing Plates</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="certificate-field">
                  <span className="field-label">C3 Plates:</span>
                  <span className="field-value">{certificate.fitment_details.c3_plates}</span>
                </div>
                <div className="certificate-field">
                  <span className="field-label">C4 Plates:</span>
                  <span className="field-value">{certificate.fitment_details.c4_plates}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Vehicle Images */}
          {certificate.images && Object.keys(certificate.images).length > 0 && (
            <div className="certificate-section">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Vehicle Images</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(certificate.images).map(([imageType, imageData]) => (
                  <div key={imageType} className="space-y-2">
                    <h4 className="font-medium text-gray-700 capitalize">
                      {imageType === 'side1' ? 'Side 1' : imageType === 'side2' ? 'Side 2' : imageType}
                    </h4>
                    <img 
                      src={imageData.startsWith('data:') ? imageData : `data:image/jpeg;base64,${imageData}`}
                      alt={`Vehicle ${imageType}`} 
                      className="w-full h-48 object-cover rounded-lg border border-gray-200"
                      data-testid={`vehicle-image-${imageType}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="certificate-section">
            <div className="text-sm text-gray-600 space-y-2">
              <p><strong>Certification Statement:</strong></p>
              <p>This is to certify that 3M have authorized Distributor/Dealer for the sale AIS-089, 090 and Retro reflective Tapes Supplied by us as per CMVR 104 - 104D</p>
              <p>We hereby certify that we have supplied/installed ICAT/ARAI Approved Retro Reflective Tapes as per CMVR 104 - 104D specified under CMVR GSR 784(E)</p>
              <p><strong>Note:</strong> Dealer can't charge more than above base price. If found then 3M will take strict action against them.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CertificateView;