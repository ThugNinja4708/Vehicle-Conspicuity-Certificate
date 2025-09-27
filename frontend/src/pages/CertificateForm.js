import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Upload, Save, Send, Camera } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CertificateForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  
  const [formData, setFormData] = useState({
    dealer_name: '',
    dealer_license: '',
    vehicle_details: {
      registration_no: '',
      chassis_no: '',
      vehicle_make: '',
      vehicle_model: '',
      registration_year: new Date().getFullYear(),
      engine_no: ''
    },
    owner_details: {
      owner_name: '',
      contact_number: ''
    },
    fitment_details: {
      red_20mm: 0,
      white_20mm: 0,
      yellow_20mm: 0,
      red_50mm: 0,
      white_50mm: 0,
      yellow_50mm: 0,
      c3_plates: 0,
      c4_plates: 0
    },
    status: 'draft'
  });
  
  const [images, setImages] = useState({
    front: null,
    back: null,
    side1: null,
    side2: null
  });
  
  const [imageFiles, setImageFiles] = useState({
    front: null,
    back: null,
    side1: null,
    side2: null
  });
  
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEdit);
  const { toast } = useToast();

  useEffect(() => {
    if (isEdit) {
      fetchCertificate();
    }
  }, [id, isEdit]);

  const fetchCertificate = async () => {
    try {
      const response = await axios.get(`${API}/certificates/${id}`);
      const cert = response.data;
      
      setFormData({
        dealer_name: cert.dealer_name,
        dealer_license: cert.dealer_license,
        vehicle_details: cert.vehicle_details,
        owner_details: cert.owner_details,
        fitment_details: cert.fitment_details,
        status: cert.status
      });
      
      // Set existing images
      if (cert.images) {
        setImages(cert.images);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch certificate",
        variant: "destructive",
      });
      navigate('/retailer/certificates');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleInputChange = (section, field, value) => {
    if (section) {
      setFormData(prev => ({
        ...prev,
        [section]: {
          ...prev[section],
          [field]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleImageUpload = (imageType, file) => {
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImages(prev => ({
          ...prev,
          [imageType]: e.target.result
        }));
      };
      reader.readAsDataURL(file);
      
      setImageFiles(prev => ({
        ...prev,
        [imageType]: file
      }));
    }
  };

  const uploadImages = async (certificateId) => {
    const uploadPromises = [];
    
    Object.entries(imageFiles).forEach(([imageType, file]) => {
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        
        uploadPromises.push(
          axios.post(`${API}/certificates/${certificateId}/upload-image?image_type=${imageType}`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
        );
      }
    });
    
    if (uploadPromises.length > 0) {
      await Promise.all(uploadPromises);
    }
  };

  const handleSave = async (status = 'draft') => {
    setLoading(true);
    
    try {
      const submitData = {
        ...formData,
        status
      };
      
      let certificateId;
      
      if (isEdit) {
        await axios.put(`${API}/certificates/${id}`, submitData);
        certificateId = id;
      } else {
        const response = await axios.post(`${API}/certificates`, submitData);
        certificateId = response.data.id;
      }
      
      // Upload images if any
      await uploadImages(certificateId);
      
      toast({
        title: "Success",
        description: `Certificate ${status === 'submitted' ? 'submitted' : 'saved'} successfully`,
      });
      
      navigate('/retailer/certificates');
    } catch (error) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || `Failed to ${status === 'submitted' ? 'submit' : 'save'} certificate`,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSave('submitted');
  };

  if (initialLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Button 
            variant="outline" 
            onClick={() => navigate('/retailer/certificates')}
            className="flex items-center gap-2"
            data-testid="back-to-certificates"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {isEdit ? 'Edit Certificate' : 'New Vehicle Conspicuity Certificate'}
            </h1>
            <p className="text-gray-600">Fill out the vehicle conspicuity fitment details</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6" data-testid="certificate-form">
          {/* Dealer Information */}
          <Card className="form-container">
            <CardHeader>
              <CardTitle>Dealer Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="dealer_name">Dealer/Applicator Name *</Label>
                  <Input
                    id="dealer_name"
                    value={formData.dealer_name}
                    onChange={(e) => handleInputChange(null, 'dealer_name', e.target.value)}
                    required
                    data-testid="dealer-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="dealer_license">Dealer/Applicator License Number *</Label>
                  <Input
                    id="dealer_license"
                    value={formData.dealer_license}
                    onChange={(e) => handleInputChange(null, 'dealer_license', e.target.value)}
                    required
                    data-testid="dealer-license-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Vehicle Details */}
          <Card className="form-container">
            <CardHeader>
              <CardTitle>Vehicle Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="registration_no">Registration Number *</Label>
                  <Input
                    id="registration_no"
                    value={formData.vehicle_details.registration_no}
                    onChange={(e) => handleInputChange('vehicle_details', 'registration_no', e.target.value)}
                    required
                    data-testid="registration-no-input"
                  />
                </div>
                <div>
                  <Label htmlFor="chassis_no">Chassis Number *</Label>
                  <Input
                    id="chassis_no"
                    value={formData.vehicle_details.chassis_no}
                    onChange={(e) => handleInputChange('vehicle_details', 'chassis_no', e.target.value)}
                    required
                    data-testid="chassis-no-input"
                  />
                </div>
                <div>
                  <Label htmlFor="vehicle_make">Vehicle Make *</Label>
                  <Input
                    id="vehicle_make"
                    value={formData.vehicle_details.vehicle_make}
                    onChange={(e) => handleInputChange('vehicle_details', 'vehicle_make', e.target.value)}
                    required
                    data-testid="vehicle-make-input"
                  />
                </div>
                <div>
                  <Label htmlFor="vehicle_model">Vehicle Model *</Label>
                  <Input
                    id="vehicle_model"
                    value={formData.vehicle_details.vehicle_model}
                    onChange={(e) => handleInputChange('vehicle_details', 'vehicle_model', e.target.value)}
                    required
                    data-testid="vehicle-model-input"
                  />
                </div>
                <div>
                  <Label htmlFor="registration_year">Registration Year *</Label>
                  <Input
                    id="registration_year"
                    type="number"
                    value={formData.vehicle_details.registration_year}
                    onChange={(e) => handleInputChange('vehicle_details', 'registration_year', parseInt(e.target.value))}
                    required
                    data-testid="registration-year-input"
                  />
                </div>
                <div>
                  <Label htmlFor="engine_no">Engine Number *</Label>
                  <Input
                    id="engine_no"
                    value={formData.vehicle_details.engine_no}
                    onChange={(e) => handleInputChange('vehicle_details', 'engine_no', e.target.value)}
                    required
                    data-testid="engine-no-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Owner Details */}
          <Card className="form-container">
            <CardHeader>
              <CardTitle>Owner Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="owner_name">Owner Name *</Label>
                  <Input
                    id="owner_name"
                    value={formData.owner_details.owner_name}
                    onChange={(e) => handleInputChange('owner_details', 'owner_name', e.target.value)}
                    required
                    data-testid="owner-name-input"
                  />
                </div>
                <div>
                  <Label htmlFor="contact_number">Contact Number *</Label>
                  <Input
                    id="contact_number"
                    value={formData.owner_details.contact_number}
                    onChange={(e) => handleInputChange('owner_details', 'contact_number', e.target.value)}
                    required
                    data-testid="contact-number-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Fitment Details */}
          <Card className="form-container">
            <CardHeader>
              <CardTitle>Conspicuity Tapes & Fitment Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 20MM Tapes */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Conspicuity Tapes 20MM (meters)</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="red_20mm">Red 20MM</Label>
                    <Input
                      id="red_20mm"
                      type="number"
                      step="0.01"
                      value={formData.fitment_details.red_20mm}
                      onChange={(e) => handleInputChange('fitment_details', 'red_20mm', parseFloat(e.target.value) || 0)}
                      data-testid="red-20mm-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="white_20mm">White 20MM</Label>
                    <Input
                      id="white_20mm"
                      type="number"
                      step="0.01"
                      value={formData.fitment_details.white_20mm}
                      onChange={(e) => handleInputChange('fitment_details', 'white_20mm', parseFloat(e.target.value) || 0)}
                      data-testid="white-20mm-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="yellow_20mm">Yellow 20MM</Label>
                    <Input
                      id="yellow_20mm"
                      type="number"
                      step="0.01"
                      value={formData.fitment_details.yellow_20mm}
                      onChange={(e) => handleInputChange('fitment_details', 'yellow_20mm', parseFloat(e.target.value) || 0)}
                      data-testid="yellow-20mm-input"
                    />
                  </div>
                </div>
              </div>

              {/* 50MM Tapes */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Conspicuity Tapes 50MM (meters)</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="red_50mm">Red 50MM</Label>
                    <Input
                      id="red_50mm"
                      type="number"
                      step="0.01"
                      value={formData.fitment_details.red_50mm}
                      onChange={(e) => handleInputChange('fitment_details', 'red_50mm', parseFloat(e.target.value) || 0)}
                      data-testid="red-50mm-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="white_50mm">White 50MM</Label>
                    <Input
                      id="white_50mm"
                      type="number"
                      step="0.01"
                      value={formData.fitment_details.white_50mm}
                      onChange={(e) => handleInputChange('fitment_details', 'white_50mm', parseFloat(e.target.value) || 0)}
                      data-testid="white-50mm-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="yellow_50mm">Yellow 50MM</Label>
                    <Input
                      id="yellow_50mm"
                      type="number"
                      step="0.01"
                      value={formData.fitment_details.yellow_50mm}
                      onChange={(e) => handleInputChange('fitment_details', 'yellow_50mm', parseFloat(e.target.value) || 0)}
                      data-testid="yellow-50mm-input"
                    />
                  </div>
                </div>
              </div>

              {/* Marketing Plates */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Rear Marketing Plates</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="c3_plates">C3 Plates</Label>
                    <Input
                      id="c3_plates"
                      type="number"
                      value={formData.fitment_details.c3_plates}
                      onChange={(e) => handleInputChange('fitment_details', 'c3_plates', parseInt(e.target.value) || 0)}
                      data-testid="c3-plates-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="c4_plates">C4 Plates</Label>
                    <Input
                      id="c4_plates"
                      type="number"
                      value={formData.fitment_details.c4_plates}
                      onChange={(e) => handleInputChange('fitment_details', 'c4_plates', parseInt(e.target.value) || 0)}
                      data-testid="c4-plates-input"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Vehicle Images */}
          <Card className="form-container">
            <CardHeader>
              <CardTitle>Vehicle Images</CardTitle>
              <p className="text-sm text-gray-600">Upload photos of the vehicle showing the conspicuity tape fitment</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {['front', 'back', 'side1', 'side2'].map((imageType) => (
                  <div key={imageType} className="space-y-2">
                    <Label className="capitalize">{imageType === 'side1' ? 'Side 1' : imageType === 'side2' ? 'Side 2' : imageType}</Label>
                    <div className={`image-preview ${images[imageType] ? 'has-image' : ''}`}>
                      {images[imageType] ? (
                        <div className="relative">
                          <img 
                            src={images[imageType].startsWith('data:') ? images[imageType] : `data:image/jpeg;base64,${images[imageType]}`} 
                            alt={`Vehicle ${imageType}`} 
                            className="w-full h-32 object-cover rounded-md"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="absolute top-2 right-2"
                            onClick={() => {
                              setImages(prev => ({ ...prev, [imageType]: null }));
                              setImageFiles(prev => ({ ...prev, [imageType]: null }));
                            }}
                          >
                            Remove
                          </Button>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center justify-center h-32">
                          <Camera className="w-8 h-8 text-gray-400 mb-2" />
                          <p className="text-sm text-gray-600 mb-2">Upload {imageType} view</p>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(e) => handleImageUpload(imageType, e.target.files[0])}
                            className="hidden"
                            id={`image-${imageType}`}
                            data-testid={`image-upload-${imageType}`}
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => document.getElementById(`image-${imageType}`).click()}
                          >
                            Choose File
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-between items-center pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/retailer/certificates')}
              data-testid="cancel-button"
            >
              Cancel
            </Button>
            
            <div className="flex gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleSave('draft')}
                disabled={loading}
                className="flex items-center gap-2"
                data-testid="save-draft-button"
              >
                <Save className="w-4 h-4" />
                {loading ? 'Saving...' : 'Save Draft'}
              </Button>
              
              <Button
                type="submit"
                disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-700 flex items-center gap-2"
                data-testid="submit-certificate-button"
              >
                <Send className="w-4 h-4" />
                {loading ? 'Submitting...' : 'Submit Certificate'}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CertificateForm;