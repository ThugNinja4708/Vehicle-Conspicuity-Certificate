import requests
import sys
import json
from datetime import datetime
import base64
import io

class VehicleConspicuityAPITester:
    def __init__(self, base_url="https://retail-chain.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.distributor_token = None
        self.retailer_token = None
        self.distributor_id = None
        self.retailer_id = None
        self.certificate_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        if files:
            # Remove Content-Type for file uploads
            headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                try:
                    return False, response.json() if response.content else {}
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_admin_login(self):
        """Test admin login with default credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_admin_dashboard_stats(self):
        """Test admin dashboard stats"""
        if not self.admin_token:
            print("❌ Skipping - No admin token")
            return False
            
        success, response = self.run_test(
            "Admin Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            token=self.admin_token
        )
        if success:
            expected_keys = ['total_users', 'total_distributors', 'total_retailers', 'total_certificates']
            for key in expected_keys:
                if key not in response:
                    print(f"   Warning: Missing key '{key}' in stats response")
        return success

    def test_create_distributor(self):
        """Test creating a distributor user"""
        if not self.admin_token:
            print("❌ Skipping - No admin token")
            return False
            
        timestamp = datetime.now().strftime('%H%M%S')
        distributor_data = {
            "username": f"test_distributor_{timestamp}",
            "password": "TestPass123!",
            "role": "distributor",
            "company_name": "Test Distribution Co",
            "contact_number": "1234567890"
        }
        
        success, response = self.run_test(
            "Create Distributor",
            "POST",
            "auth/register",
            200,
            data=distributor_data,
            token=self.admin_token
        )
        if success and 'id' in response:
            self.distributor_id = response['id']
            print(f"   Distributor created with ID: {self.distributor_id}")
            
            # Test distributor login
            login_success, login_response = self.run_test(
                "Distributor Login",
                "POST",
                "auth/login",
                200,
                data={"username": distributor_data["username"], "password": distributor_data["password"]}
            )
            if login_success and 'access_token' in login_response:
                self.distributor_token = login_response['access_token']
                print(f"   Distributor token obtained: {self.distributor_token[:20]}...")
            return True
        return False

    def test_create_retailer(self):
        """Test creating a retailer user by distributor"""
        if not self.distributor_token:
            print("❌ Skipping - No distributor token")
            return False
            
        timestamp = datetime.now().strftime('%H%M%S')
        retailer_data = {
            "username": f"test_retailer_{timestamp}",
            "password": "TestPass123!",
            "role": "retailer",
            "company_name": "Test Retail Store",
            "contact_number": "9876543210"
        }
        
        success, response = self.run_test(
            "Create Retailer by Distributor",
            "POST",
            "auth/register",
            200,
            data=retailer_data,
            token=self.distributor_token
        )
        if success and 'id' in response:
            self.retailer_id = response['id']
            print(f"   Retailer created with ID: {self.retailer_id}")
            
            # Test retailer login
            login_success, login_response = self.run_test(
                "Retailer Login",
                "POST",
                "auth/login",
                200,
                data={"username": retailer_data["username"], "password": retailer_data["password"]}
            )
            if login_success and 'access_token' in login_response:
                self.retailer_token = login_response['access_token']
                print(f"   Retailer token obtained: {self.retailer_token[:20]}...")
            return True
        return False

    def test_distributor_dashboard_stats(self):
        """Test distributor dashboard stats"""
        if not self.distributor_token:
            print("❌ Skipping - No distributor token")
            return False
            
        success, response = self.run_test(
            "Distributor Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            token=self.distributor_token
        )
        if success:
            expected_keys = ['total_retailers', 'total_certificates', 'submitted_certificates', 'draft_certificates']
            for key in expected_keys:
                if key not in response:
                    print(f"   Warning: Missing key '{key}' in distributor stats response")
        return success

    def test_retailer_dashboard_stats(self):
        """Test retailer dashboard stats"""
        if not self.retailer_token:
            print("❌ Skipping - No retailer token")
            return False
            
        success, response = self.run_test(
            "Retailer Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            token=self.retailer_token
        )
        if success:
            expected_keys = ['total_certificates', 'submitted_certificates', 'draft_certificates']
            for key in expected_keys:
                if key not in response:
                    print(f"   Warning: Missing key '{key}' in retailer stats response")
        return success

    def test_get_users_admin(self):
        """Test getting all users as admin"""
        if not self.admin_token:
            print("❌ Skipping - No admin token")
            return False
            
        success, response = self.run_test(
            "Get All Users (Admin)",
            "GET",
            "users",
            200,
            token=self.admin_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} users")
        return success

    def test_get_users_distributor(self):
        """Test getting retailers as distributor"""
        if not self.distributor_token:
            print("❌ Skipping - No distributor token")
            return False
            
        success, response = self.run_test(
            "Get Retailers (Distributor)",
            "GET",
            "users",
            200,
            token=self.distributor_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} retailers under distributor")
        return success

    def test_create_certificate(self):
        """Test creating a certificate as retailer"""
        if not self.retailer_token:
            print("❌ Skipping - No retailer token")
            return False
            
        certificate_data = {
            "dealer_name": "Test Dealer",
            "dealer_license": "DL123456789",
            "vehicle_details": {
                "registration_no": "MH01AB1234",
                "chassis_no": "CHASSIS123456789",
                "vehicle_make": "Tata",
                "vehicle_model": "Ace",
                "registration_year": 2023,
                "engine_no": "ENGINE123456"
            },
            "owner_details": {
                "owner_name": "Test Owner",
                "contact_number": "9876543210"
            },
            "fitment_details": {
                "red_20mm": 5.5,
                "white_20mm": 3.2,
                "yellow_20mm": 2.1,
                "red_50mm": 1.5,
                "white_50mm": 2.0,
                "yellow_50mm": 1.0,
                "c3_plates": 2,
                "c4_plates": 1
            },
            "status": "draft"
        }
        
        success, response = self.run_test(
            "Create Certificate (Draft)",
            "POST",
            "certificates",
            200,
            data=certificate_data,
            token=self.retailer_token
        )
        if success and 'id' in response:
            self.certificate_id = response['id']
            print(f"   Certificate created with ID: {self.certificate_id}")
            print(f"   Certificate No: {response.get('certificate_no', 'N/A')}")
            return True
        return False

    def test_get_certificates_retailer(self):
        """Test getting certificates as retailer"""
        if not self.retailer_token:
            print("❌ Skipping - No retailer token")
            return False
            
        success, response = self.run_test(
            "Get Certificates (Retailer)",
            "GET",
            "certificates",
            200,
            token=self.retailer_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} certificates for retailer")
        return success

    def test_get_certificate_by_id(self):
        """Test getting specific certificate by ID"""
        if not self.certificate_id or not self.retailer_token:
            print("❌ Skipping - No certificate ID or retailer token")
            return False
            
        success, response = self.run_test(
            "Get Certificate by ID",
            "GET",
            f"certificates/{self.certificate_id}",
            200,
            token=self.retailer_token
        )
        if success:
            print(f"   Retrieved certificate: {response.get('certificate_no', 'N/A')}")
        return success

    def test_update_certificate(self):
        """Test updating certificate"""
        if not self.certificate_id or not self.retailer_token:
            print("❌ Skipping - No certificate ID or retailer token")
            return False
            
        update_data = {
            "dealer_name": "Updated Dealer Name",
            "status": "submitted"
        }
        
        success, response = self.run_test(
            "Update Certificate",
            "PUT",
            f"certificates/{self.certificate_id}",
            200,
            data=update_data,
            token=self.retailer_token
        )
        if success:
            print(f"   Certificate updated - Status: {response.get('status', 'N/A')}")
        return success

    def test_image_upload(self):
        """Test image upload for certificate"""
        if not self.certificate_id or not self.retailer_token:
            print("❌ Skipping - No certificate ID or retailer token")
            return False
            
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA60e6kgAAAABJRU5ErkJggg==')
        
        files = {
            'file': ('test_image.png', io.BytesIO(test_image_data), 'image/png')
        }
        
        success, response = self.run_test(
            "Upload Certificate Image",
            "POST",
            f"certificates/{self.certificate_id}/upload-image?image_type=front",
            200,
            files=files,
            token=self.retailer_token
        )
        if success:
            print(f"   Image uploaded successfully: {response.get('message', 'N/A')}")
        return success

    def test_get_certificates_distributor(self):
        """Test getting certificates as distributor"""
        if not self.distributor_token:
            print("❌ Skipping - No distributor token")
            return False
            
        success, response = self.run_test(
            "Get Certificates (Distributor)",
            "GET",
            "certificates",
            200,
            token=self.distributor_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} certificates for distributor")
        return success

    def test_get_certificates_admin(self):
        """Test getting all certificates as admin"""
        if not self.admin_token:
            print("❌ Skipping - No admin token")
            return False
            
        success, response = self.run_test(
            "Get All Certificates (Admin)",
            "GET",
            "certificates",
            200,
            token=self.admin_token
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} total certificates")
        return success

    def test_auth_me_endpoint(self):
        """Test the /auth/me endpoint for all user types"""
        results = []
        
        if self.admin_token:
            success, response = self.run_test(
                "Get Current User Info (Admin)",
                "GET",
                "auth/me",
                200,
                token=self.admin_token
            )
            results.append(success)
            if success:
                print(f"   Admin user: {response.get('username', 'N/A')} - Role: {response.get('role', 'N/A')}")
        
        if self.distributor_token:
            success, response = self.run_test(
                "Get Current User Info (Distributor)",
                "GET",
                "auth/me",
                200,
                token=self.distributor_token
            )
            results.append(success)
            if success:
                print(f"   Distributor user: {response.get('username', 'N/A')} - Role: {response.get('role', 'N/A')}")
        
        if self.retailer_token:
            success, response = self.run_test(
                "Get Current User Info (Retailer)",
                "GET",
                "auth/me",
                200,
                token=self.retailer_token
            )
            results.append(success)
            if success:
                print(f"   Retailer user: {response.get('username', 'N/A')} - Role: {response.get('role', 'N/A')}")
        
        return all(results) if results else False

    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        print("\n🔒 Testing unauthorized access scenarios...")
        
        # Test accessing protected endpoint without token
        success, _ = self.run_test(
            "Access Dashboard Without Token",
            "GET",
            "dashboard/stats",
            401
        )
        
        # Test retailer trying to create another user (should fail)
        if self.retailer_token:
            retailer_create_user = {
                "username": "unauthorized_user",
                "password": "TestPass123!",
                "role": "retailer",
                "company_name": "Unauthorized Co"
            }
            
            success2, _ = self.run_test(
                "Retailer Trying to Create User (Should Fail)",
                "POST",
                "auth/register",
                403,
                data=retailer_create_user,
                token=self.retailer_token
            )
            return success and success2
        
        return success

def main():
    print("🚀 Starting Vehicle Conspicuity Management System API Tests")
    print("=" * 60)
    
    tester = VehicleConspicuityAPITester()
    
    # Test sequence
    test_sequence = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Admin Authentication", tester.test_admin_login),
        ("Admin Dashboard Stats", tester.test_admin_dashboard_stats),
        ("Create Distributor", tester.test_create_distributor),
        ("Create Retailer", tester.test_create_retailer),
        ("Distributor Dashboard Stats", tester.test_distributor_dashboard_stats),
        ("Retailer Dashboard Stats", tester.test_retailer_dashboard_stats),
        ("Get Users (Admin)", tester.test_get_users_admin),
        ("Get Users (Distributor)", tester.test_get_users_distributor),
        ("Create Certificate", tester.test_create_certificate),
        ("Get Certificates (Retailer)", tester.test_get_certificates_retailer),
        ("Get Certificate by ID", tester.test_get_certificate_by_id),
        ("Update Certificate", tester.test_update_certificate),
        ("Upload Certificate Image", tester.test_image_upload),
        ("Get Certificates (Distributor)", tester.test_get_certificates_distributor),
        ("Get Certificates (Admin)", tester.test_get_certificates_admin),
        ("Auth Me Endpoints", tester.test_auth_me_endpoint),
        ("Unauthorized Access", tester.test_unauthorized_access),
    ]
    
    print(f"\n📋 Running {len(test_sequence)} test categories...")
    
    for test_name, test_func in test_sequence:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test category '{test_name}' failed with error: {str(e)}")
            tester.failed_tests.append({
                "test": test_name,
                "error": str(e)
            })
    
    # Print final results
    print("\n" + "="*60)
    print("📊 FINAL TEST RESULTS")
    print("="*60)
    print(f"Total Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS ({len(tester.failed_tests)}):")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"{i}. {failure['test']}")
            if 'error' in failure:
                print(f"   Error: {failure['error']}")
            elif 'expected' in failure:
                print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
                if 'response' in failure:
                    print(f"   Response: {failure['response']}")
    
    # Return appropriate exit code
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())