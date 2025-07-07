import unittest
from unittest.mock import patch, Mock, MagicMock
import json
import os
import sys
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from bson import ObjectId
import io
import uuid

# Add apps to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps'))

from apps.clients_contracts.views import contracts_collection, clients_collection


class BaseTestCase(TestCase):
    """Base test case with common setup."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        # Use unique username to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        self.user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123'
        )
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Sample contract data
        self.sample_contract_data = {
            'title': 'Test Contract',
            'client': 'Test Client',
            'signed': False,
            'text': 'This is a test contract with payment terms and termination clauses.',
            'date': '2025-01-01'
        }

    def tearDown(self):
        """Clean up after tests."""
        # Clean up MongoDB collections
        try:
            contracts_collection.delete_many({})
            clients_collection.delete_many({})
        except:
            pass


class TestContractViews(BaseTestCase):
    """Test contract CRUD operations."""
    
    @patch('apps.clients_contracts.ai_service.AIService.analyze_contract')
    @patch('apps.clients_contracts.ai_service.AIService.evaluate_contract')
    def test_create_contract_success(self, mock_evaluate, mock_analyze):
        """Test successful contract creation with AI analysis."""
        mock_analyze.return_value = {
            'analysis': 'Test analysis result',
            'model_used': 'DeepSeek Reasoning Model (Live)'
        }
        mock_evaluate.return_value = {
            'approved': True,
            'reasoning': 'Contract meets all requirements'
        }
        
        response = self.client.post('/api/contracts/', self.sample_contract_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('contract_id', response.data)
        self.assertIn('analysis', response.data)
        self.assertTrue(response.data['approved'])
        
        # Verify AI methods were called
        mock_analyze.assert_called_once()
        mock_evaluate.assert_called_once()

    def test_create_contract_missing_fields(self):
        """Test contract creation with missing required fields."""
        incomplete_data = {'title': 'Test Contract'}
        
        response = self.client.post('/api/contracts/', incomplete_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('apps.clients_contracts.ai_service.AIService.analyze_contract')
    @patch('apps.clients_contracts.ai_service.AIService.evaluate_contract')
    def test_create_contract_with_file_upload(self, mock_evaluate, mock_analyze):
        """Test contract creation with PDF file upload."""
        mock_analyze.return_value = {
            'analysis': 'File analysis result',
            'model_used': 'DeepSeek Reasoning Model (Live)'
        }
        mock_evaluate.return_value = {
            'approved': False,
            'reasoning': 'Contract needs revision'
        }
        
        # Create a mock file
        file_content = b"Mock PDF content for testing"
        file_data = io.BytesIO(file_content)
        file_data.name = 'test_contract.txt'
        
        data = {
            'title': 'PDF Contract',
            'client': 'PDF Client',
            'signed': 'false',
            'file': file_data
        }
        
        response = self.client.post('/api/contracts/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('contract_id', response.data)
        self.assertFalse(response.data['approved'])

    def test_list_contracts(self):
        """Test listing all contracts."""
        # Insert test contracts directly into MongoDB
        test_contract = {
            'title': 'List Test Contract',
            'client': 'List Test Client',
            'signed': False,
            'text': 'Test contract text',
            'date': '2025-01-01',
            'analysis': 'Test analysis',
            'approved': True
        }
        contracts_collection.insert_one(test_contract)
        
        response = self.client.get('/api/contracts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

    def test_get_contract_detail(self):
        """Test retrieving a specific contract."""
        # Insert test contract
        test_contract = {
            'title': 'Detail Test Contract',
            'client': 'Detail Test Client',
            'signed': False,
            'text': 'Test contract text',
            'date': '2025-01-01',
            'analysis': 'Test analysis',
            'approved': True
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        response = self.client.get(f'/api/contracts/{contract_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Detail Test Contract')
        self.assertIn('approved', response.data)

    def test_get_contract_not_found(self):
        """Test retrieving non-existent contract."""
        fake_id = str(ObjectId())
        
        response = self.client.get(f'/api/contracts/{fake_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_contract(self):
        """Test updating a contract."""
        # Insert test contract
        test_contract = {
            'title': 'Update Test Contract',
            'client': 'Update Test Client',
            'signed': False,
            'text': 'Test contract text',
            'date': '2025-01-01'
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        update_data = {'title': 'Updated Contract Title', 'signed': True}
        
        # Use JSON format to avoid QueryDict immutability
        update_response = self.client.put(
            f'/api/contracts/{contract_id}/', 
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], 'Updated Contract Title')
        self.assertTrue(update_response.data['signed'])

    def test_delete_contract(self):
        """Test deleting a contract."""
        # Insert test contract
        test_contract = {
            'title': 'Delete Test Contract',
            'client': 'Delete Test Client',
            'signed': False,
            'text': 'Test contract text',
            'date': '2025-01-01'
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        response = self.client.delete(f'/api/contracts/{contract_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify contract was deleted
        contract = contracts_collection.find_one({'_id': result.inserted_id})
        self.assertIsNone(contract)


class TestContractAnalysisViews(BaseTestCase):
    """Test contract analysis endpoints."""
    
    def test_get_contract_analysis(self):
        """Test retrieving contract analysis."""
        # Insert contract with analysis
        test_contract = {
            'title': 'Analysis Test Contract',
            'client': 'Analysis Test Client',
            'analysis': 'Detailed contract analysis',
            'model_used': 'DeepSeek Reasoning Model (Live)',
            'analysis_date': '2025-01-01T00:00:00'
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        response = self.client.get(f'/api/contracts/{contract_id}/analysis/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis'], 'Detailed contract analysis')
        self.assertIn('model_used', response.data)

    def test_get_analysis_not_found(self):
        """Test retrieving analysis for contract without analysis."""
        # Insert contract without analysis
        test_contract = {
            'title': 'No Analysis Contract',
            'client': 'No Analysis Client'
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        response = self.client.get(f'/api/contracts/{contract_id}/analysis/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.clients_contracts.ai_service.AIService.extract_clauses')
    def test_extract_clauses_success(self, mock_extract):
        """Test successful clause extraction."""
        mock_extract.return_value = {
            'clauses': [
                {
                    'type': 'Payment Terms',
                    'content': 'Payment due in 30 days',
                    'risk_level': 'low',
                    'obligations': ['Make payment']
                }
            ],
            'clause_count': 1,
            'model_used': 'deepseek-chat'
        }
        
        # Insert contract with text
        test_contract = {
            'title': 'Clause Test Contract',
            'client': 'Clause Test Client',
            'text': 'Contract with payment terms and clauses'
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        response = self.client.post(f'/api/contracts/{contract_id}/clauses/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('clauses', response.data)
        self.assertEqual(response.data['clause_count'], 1)
        self.assertEqual(len(response.data['clauses']), 1)

    def test_extract_clauses_no_text(self):
        """Test clause extraction for contract without text."""
        # Insert contract without text
        test_contract = {
            'title': 'No Text Contract',
            'client': 'No Text Client'
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        response = self.client.post(f'/api/contracts/{contract_id}/clauses/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('apps.clients_contracts.ai_service.AIService.analyze_contract')
    @patch('apps.clients_contracts.ai_service.AIService.evaluate_contract')
    def test_reanalyze_contract(self, mock_evaluate, mock_analyze):
        """Test contract reanalysis with new file."""
        mock_analyze.return_value = {
            'analysis': 'Updated analysis result',
            'model_used': 'DeepSeek Reasoning Model (Live)'
        }
        mock_evaluate.return_value = {
            'approved': True,
            'reasoning': 'Updated contract is approved'
        }
        
        # Insert existing contract
        test_contract = {
            'title': 'Reanalyze Test Contract',
            'client': 'Reanalyze Test Client',
            'text': 'Original contract text'
        }
        result = contracts_collection.insert_one(test_contract)
        contract_id = str(result.inserted_id)
        
        # Create new file for reanalysis
        file_content = b"Updated contract content"
        file_data = io.BytesIO(file_content)
        file_data.name = 'updated_contract.txt'
        
        data = {
            'title': 'Updated Contract Title',
            'file': file_data
        }
        
        response = self.client.post(f'/api/contracts/{contract_id}/reanalyze/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('analysis', response.data)
        self.assertTrue(response.data['approved'])


class TestClientViews(BaseTestCase):
    """Test client CRUD operations."""
    
    def test_create_client(self):
        """Test creating a new client."""
        client_data = {
            'name': 'Test Client Corp',
            'email': 'client@test.com',
            'company_id': 'TC001'
        }
        
        response = self.client.post('/api/clients/', client_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Client Corp')
        self.assertIn('_id', response.data)

    def test_list_clients(self):
        """Test listing all clients."""
        # Insert test client
        test_client = {
            'name': 'List Test Client',
            'email': 'list@test.com',
            'active': True
        }
        clients_collection.insert_one(test_client)
        
        response = self.client.get('/api/clients/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_client_contracts(self):
        """Test getting contracts for a specific client."""
        # Insert test client
        test_client = {
            'name': 'Contract Client',
            'email': 'contracts@test.com'
        }
        client_result = clients_collection.insert_one(test_client)
        client_id = str(client_result.inserted_id)
        
        # Insert contract for this client
        test_contract = {
            'title': 'Client Contract',
            'client': 'Contract Client',
            'signed': True
        }
        contracts_collection.insert_one(test_contract)
        
        response = self.client.get(f'/api/clients/{client_id}/contracts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class TestAuthenticationViews(BaseTestCase):
    """Test authentication endpoints."""
    
    def test_login_success(self):
        """Test successful login."""
        # Remove authentication for login test
        self.client.credentials()
        
        login_data = {
            'username': self.user.username,
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Backend returns 'token' field, not 'access'
        self.assertIn('token', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        # Remove authentication for login test
        self.client.credentials()
        
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_success(self):
        """Test successful user registration."""
        # Remove authentication for registration test
        self.client.credentials()
        
        unique_id = str(uuid.uuid4())[:8]
        register_data = {
            'username': f'newuser_{unique_id}',
            'password': 'newpass123'
        }
        
        response = self.client.post('/api/auth/register/', register_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Backend returns message on registration, not tokens
        self.assertIn('message', response.data)


class TestSystemViews(BaseTestCase):
    """Test system monitoring endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/healthz/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

    def test_readiness_check(self):
        """Test readiness check endpoint."""
        response = self.client.get('/readyz/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = self.client.get('/metrics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('request_count', response.data)
        self.assertIn('average_latency', response.data)

    def test_logs_endpoint(self):
        """Test logs endpoint."""
        response = self.client.get('/logs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)


if __name__ == '__main__':
    unittest.main() 