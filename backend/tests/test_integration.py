import unittest
from unittest.mock import patch, Mock
import json
import os
import sys
import io
import uuid
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from bson import ObjectId

# Add apps to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps'))

from apps.clients_contracts.views import contracts_collection, clients_collection


class BaseIntegrationTest(TransactionTestCase):
    """Base class for integration tests."""
    
    def setUp(self):
        """Set up test fixtures for integration tests."""
        self.client = APIClient()
        
        # Create test user with unique username
        unique_id = str(uuid.uuid4())[:8]
        self.user = User.objects.create_user(
            username=f'integrationuser_{unique_id}',
            email=f'integration_{unique_id}@test.com',
            password='integrationpass123'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Mock AI responses for consistent testing
        self.mock_analysis_response = {
            'analysis': 'This is a comprehensive contract analysis with detailed evaluation of terms and conditions.',
            'model_used': 'DeepSeek Reasoning Model (Live)'
        }
        
        self.mock_evaluation_response = {
            'approved': True,
            'reasoning': 'Contract meets all legal requirements and business criteria.'
        }
        
        self.mock_clauses_response = {
            'clauses': [
                {
                    'type': 'Payment Terms',
                    'content': 'Payment shall be made within 30 days of invoice date.',
                    'risk_level': 'low',
                    'obligations': ['Make timely payments', 'Maintain payment records']
                },
                {
                    'type': 'Termination',
                    'content': 'Either party may terminate with 60 days written notice.',
                    'risk_level': 'medium',
                    'obligations': ['Provide written notice', 'Complete pending obligations']
                },
                {
                    'type': 'Confidentiality',
                    'content': 'All confidential information must be protected.',
                    'risk_level': 'high',
                    'obligations': ['Protect confidential information', 'Return materials upon termination']
                }
            ],
            'clause_count': 3,
            'model_used': 'deepseek-chat'
        }

    def tearDown(self):
        """Clean up after integration tests."""
        try:
            contracts_collection.delete_many({})
            clients_collection.delete_many({})
        except:
            pass


class TestCompleteContractWorkflow(BaseIntegrationTest):
    """Test complete contract management workflow."""
    
    @patch('apps.clients_contracts.ai_service.AIService.analyze_contract')
    @patch('apps.clients_contracts.ai_service.AIService.evaluate_contract')
    def test_complete_contract_upload_and_analysis_workflow(self, mock_evaluate, mock_analyze):
        """Test the complete workflow: upload -> analyze -> evaluate -> view."""
        mock_analyze.return_value = self.mock_analysis_response
        mock_evaluate.return_value = self.mock_evaluation_response
        
        # Step 1: Upload contract
        contract_data = {
            'title': 'Integration Test Contract',
            'client': 'Integration Test Client',
            'signed': False,
            'text': 'This is a test contract for integration testing with payment terms, termination clauses, and confidentiality agreements.',
            'date': '2025-01-15'
        }
        
        upload_response = self.client.post('/api/contracts/', contract_data)
        
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('contract_id', upload_response.data)
        self.assertIn('analysis', upload_response.data)
        self.assertTrue(upload_response.data['approved'])
        
        contract_id = upload_response.data['contract_id']
        
        # Step 2: Retrieve contract details
        detail_response = self.client.get(f'/api/contracts/{contract_id}/')
        
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['title'], 'Integration Test Contract')
        self.assertIn('analysis', detail_response.data)
        
        # Step 3: Get analysis details
        analysis_response = self.client.get(f'/api/contracts/{contract_id}/analysis/')
        
        self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
        self.assertEqual(analysis_response.data['analysis'], self.mock_analysis_response['analysis'])
        
        # Step 4: List all contracts and verify our contract is there
        list_response = self.client.get('/api/contracts/')
        
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        contract_titles = [contract['title'] for contract in list_response.data]
        self.assertIn('Integration Test Contract', contract_titles)

    @patch('apps.clients_contracts.ai_service.AIService.extract_clauses')
    def test_contract_clause_extraction_workflow(self, mock_extract):
        """Test contract clause extraction workflow."""
        mock_extract.return_value = self.mock_clauses_response
        
        # Step 1: Create a contract with text
        contract_data = {
            'title': 'Clause Extraction Test Contract',
            'client': 'Clause Test Client',
            'text': 'Contract with payment terms: Payment shall be made within 30 days. Termination: Either party may terminate with 60 days notice. Confidentiality: All information must remain confidential.',
            'signed': False
        }
        
        # Insert contract directly to MongoDB for this test
        result = contracts_collection.insert_one(contract_data)
        contract_id = str(result.inserted_id)
        
        # Step 2: Extract clauses
        extract_response = self.client.post(f'/api/contracts/{contract_id}/clauses/')
        
        self.assertEqual(extract_response.status_code, status.HTTP_200_OK)
        self.assertIn('clauses', extract_response.data)
        self.assertEqual(extract_response.data['clause_count'], 3)
        self.assertEqual(len(extract_response.data['clauses']), 3)
        
        # Step 3: Verify clause details
        clauses = extract_response.data['clauses']
        clause_types = [clause['type'] for clause in clauses]
        self.assertIn('Payment Terms', clause_types)
        self.assertIn('Termination', clause_types)
        self.assertIn('Confidentiality', clause_types)
        
        # Step 4: Verify risk levels are assigned
        risk_levels = [clause['risk_level'] for clause in clauses]
        self.assertIn('low', risk_levels)
        self.assertIn('medium', risk_levels)
        self.assertIn('high', risk_levels)

    @patch('apps.clients_contracts.ai_service.AIService.analyze_contract')
    @patch('apps.clients_contracts.ai_service.AIService.evaluate_contract')
    def test_contract_file_upload_workflow(self, mock_evaluate, mock_analyze):
        """Test contract upload with file attachment."""
        mock_analyze.return_value = self.mock_analysis_response
        mock_evaluate.return_value = self.mock_evaluation_response
        
        # Create a mock contract file
        file_content = b"""
        SERVICE AGREEMENT
        
        This Service Agreement is entered into between Client Corp and Service Provider Inc.
        
        PAYMENT TERMS:
        Payment shall be made within 30 days of invoice receipt.
        
        TERMINATION:
        This agreement may be terminated by either party with 60 days written notice.
        
        CONFIDENTIALITY:
        All proprietary information disclosed shall remain confidential.
        """
        
        file_data = io.BytesIO(file_content)
        file_data.name = 'service_agreement.txt'
        
        # Upload contract with file
        upload_data = {
            'title': 'File Upload Test Contract',
            'client': 'File Upload Client',
            'signed': 'false',
            'file': file_data
        }
        
        response = self.client.post('/api/contracts/', upload_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('contract_id', response.data)
        self.assertIn('analysis', response.data)
        
        # Verify the contract was stored with the extracted text
        contract_id = response.data['contract_id']
        detail_response = self.client.get(f'/api/contracts/{contract_id}/')
        
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIn('text', detail_response.data)
        self.assertIn('SERVICE AGREEMENT', detail_response.data['text'])

    @patch('apps.clients_contracts.ai_service.AIService.analyze_contract')
    @patch('apps.clients_contracts.ai_service.AIService.evaluate_contract')
    def test_contract_reanalysis_workflow(self, mock_evaluate, mock_analyze):
        """Test contract reanalysis with updated file."""
        # Mock responses for initial and updated analysis
        initial_analysis = {
            'analysis': 'Initial contract analysis result.',
            'model_used': 'DeepSeek Reasoning Model (Live)'
        }
        updated_analysis = {
            'analysis': 'Updated contract analysis with new terms and conditions.',
            'model_used': 'DeepSeek Reasoning Model (Live)'
        }
        initial_evaluation = {
            'approved': False,
            'reasoning': 'Initial contract needs revision.'
        }
        updated_evaluation = {
            'approved': True,
            'reasoning': 'Updated contract meets all requirements.'
        }
        
        mock_analyze.side_effect = [initial_analysis, updated_analysis]
        mock_evaluate.side_effect = [initial_evaluation, updated_evaluation]
        
        # Step 1: Create initial contract
        initial_data = {
            'title': 'Reanalysis Test Contract',
            'client': 'Reanalysis Client',
            'text': 'Initial contract text with basic terms.',
            'signed': False
        }
        
        initial_response = self.client.post('/api/contracts/', initial_data)
        contract_id = initial_response.data['contract_id']
        
        # Verify initial state
        self.assertFalse(initial_response.data['approved'])
        self.assertEqual(initial_response.data['analysis'], 'Initial contract analysis result.')
        
        # Step 2: Reanalyze with updated file
        updated_file_content = b"Updated contract with improved terms and comprehensive clauses."
        updated_file = io.BytesIO(updated_file_content)
        updated_file.name = 'updated_contract.txt'
        
        reanalysis_data = {
            'title': 'Updated Reanalysis Test Contract',
            'file': updated_file
        }
        
        reanalysis_response = self.client.post(
            f'/api/contracts/{contract_id}/reanalyze/', 
            reanalysis_data, 
            format='multipart'
        )
        
        self.assertEqual(reanalysis_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Verify updated analysis
        self.assertTrue(reanalysis_response.data['approved'])
        self.assertEqual(reanalysis_response.data['analysis'], 'Updated contract analysis with new terms and conditions.')
        
        # Step 4: Verify contract was updated in database
        updated_detail_response = self.client.get(f'/api/contracts/{contract_id}/')
        
        self.assertEqual(updated_detail_response.data['title'], 'Updated Reanalysis Test Contract')
        self.assertTrue(updated_detail_response.data['approved'])

    def test_contract_crud_operations_workflow(self):
        """Test complete CRUD operations for contracts."""
        # Create
        create_data = {
            'title': 'CRUD Test Contract',
            'client': 'CRUD Test Client',
            'text': 'CRUD test contract text.',
            'signed': False,
            'date': '2025-01-15'
        }
        
        # Insert directly to avoid AI service calls
        result = contracts_collection.insert_one(create_data)
        contract_id = str(result.inserted_id)
        
        # Read
        read_response = self.client.get(f'/api/contracts/{contract_id}/')
        
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.data['title'], 'CRUD Test Contract')
        
        # Update - use JSON format to avoid QueryDict immutability
        update_data = {
            'title': 'Updated CRUD Test Contract',
            'signed': True,
            'client': 'Updated CRUD Client'
        }
        
        update_response = self.client.put(
            f'/api/contracts/{contract_id}/', 
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['title'], 'Updated CRUD Test Contract')
        self.assertTrue(update_response.data['signed'])
        
        # Verify update persisted
        verify_response = self.client.get(f'/api/contracts/{contract_id}/')
        self.assertEqual(verify_response.data['title'], 'Updated CRUD Test Contract')
        
        # Delete
        delete_response = self.client.delete(f'/api/contracts/{contract_id}/')
        
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        
        # Verify deletion
        deleted_response = self.client.get(f'/api/contracts/{contract_id}/')
        self.assertEqual(deleted_response.status_code, status.HTTP_404_NOT_FOUND)


class TestClientManagementWorkflow(BaseIntegrationTest):
    """Test client management workflows."""
    
    def test_client_and_contract_relationship_workflow(self):
        """Test workflow involving clients and their contracts."""
        # Step 1: Create a client
        client_data = {
            'name': 'Workflow Test Corp',
            'email': 'workflow@test.com',
            'company_id': 'WTC001',
            'active': True
        }
        
        client_response = self.client.post('/api/clients/', client_data)
        
        self.assertEqual(client_response.status_code, status.HTTP_201_CREATED)
        client_id = str(client_response.data['_id'])
        
        # Step 2: Create contracts for this client
        contract_data_1 = {
            'title': 'Client Contract 1',
            'client': 'Workflow Test Corp',
            'text': 'First contract for the client.',
            'signed': True
        }
        contract_data_2 = {
            'title': 'Client Contract 2',
            'client': 'Workflow Test Corp',
            'text': 'Second contract for the client.',
            'signed': False
        }
        
        # Insert contracts directly to avoid AI calls
        contracts_collection.insert_one(contract_data_1)
        contracts_collection.insert_one(contract_data_2)
        
        # Step 3: Get client's contracts
        client_contracts_response = self.client.get(f'/api/clients/{client_id}/contracts/')
        
        self.assertEqual(client_contracts_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(client_contracts_response.data), 2)
        
        contract_titles = [contract['title'] for contract in client_contracts_response.data]
        self.assertIn('Client Contract 1', contract_titles)
        self.assertIn('Client Contract 2', contract_titles)
        
        # Step 4: Verify contract status distribution
        signed_contracts = [c for c in client_contracts_response.data if c['signed']]
        unsigned_contracts = [c for c in client_contracts_response.data if not c['signed']]
        
        self.assertEqual(len(signed_contracts), 1)
        self.assertEqual(len(unsigned_contracts), 1)


class TestAuthenticationIntegration(BaseIntegrationTest):
    """Test authentication integration with contract operations."""
    
    def test_authentication_required_for_all_operations(self):
        """Test that all contract operations require authentication."""
        # Remove authentication
        self.client.credentials()
        
        endpoints_to_test = [
            ('GET', '/api/contracts/'),
            ('POST', '/api/contracts/'),
            ('GET', '/api/clients/'),
            ('POST', '/api/clients/')
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == 'GET':
                response = self.client.get(endpoint)
            elif method == 'POST':
                response = self.client.post(endpoint, {})
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_full_authentication_workflow(self):
        """Test complete authentication workflow."""
        # Remove existing authentication
        self.client.credentials()
        
        # Step 1: Register new user
        unique_id = str(uuid.uuid4())[:8]
        register_data = {
            'username': f'authworkflowuser_{unique_id}',
            'email': f'authworkflow_{unique_id}@test.com',
            'password': 'authworkflowpass123'
        }
        
        register_response = self.client.post('/api/auth/register/', register_data)
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        # Check if the response has tokens or just a success message
        if 'token' in register_response.data:
            access_token = register_response.data['token']
        elif 'access' in register_response.data:
            access_token = register_response.data['access']
        else:
            # If registration doesn't return tokens, login to get them
            login_data = {
                'username': register_data['username'],
                'password': register_data['password']
            }
            login_response = self.client.post('/api/auth/login/', login_data)
            self.assertEqual(login_response.status_code, status.HTTP_200_OK)
            # Use 'token' field from login response
            access_token = login_response.data['token']
        
        # Step 2: Use access token to access protected resource
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        contracts_response = self.client.get('/api/contracts/')
        self.assertEqual(contracts_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Logout (remove credentials) and verify access is denied
        self.client.credentials()
        
        protected_response = self.client.get('/api/contracts/')
        self.assertEqual(protected_response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Step 4: Login again with existing credentials
        login_data = {
            'username': register_data['username'],
            'password': register_data['password']
        }
        
        login_response = self.client.post('/api/auth/login/', login_data)
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Step 5: Use new token to access resources
        new_access_token = login_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        
        final_response = self.client.get('/api/contracts/')
        self.assertEqual(final_response.status_code, status.HTTP_200_OK)


class TestErrorHandlingIntegration(BaseIntegrationTest):
    """Test error handling across the entire system."""
    
    def test_graceful_error_handling_workflow(self):
        """Test that the system handles various error conditions gracefully."""
        # Test 1: Invalid contract ID
        invalid_id = str(ObjectId())
        invalid_response = self.client.get(f'/api/contracts/{invalid_id}/')
        
        self.assertEqual(invalid_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', invalid_response.data)
        
        # Test 2: Malformed request data
        malformed_data = {'invalid': 'data', 'missing': 'required_fields'}
        malformed_response = self.client.post('/api/contracts/', malformed_data)
        
        self.assertEqual(malformed_response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test 3: Clause extraction without contract text
        no_text_contract = {'title': 'No Text Contract', 'client': 'No Text Client'}
        result = contracts_collection.insert_one(no_text_contract)
        contract_id = str(result.inserted_id)
        
        clauses_response = self.client.post(f'/api/contracts/{contract_id}/clauses/')
        
        self.assertEqual(clauses_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', clauses_response.data)

    @patch('apps.clients_contracts.ai_service.AIService.analyze_contract')
    @patch('apps.clients_contracts.ai_service.AIService.evaluate_contract')
    def test_ai_service_failure_handling(self, mock_evaluate, mock_analyze):
        """Test handling of AI service failures."""
        # Mock AI service failures
        mock_analyze.side_effect = Exception("AI service temporarily unavailable")
        mock_evaluate.side_effect = Exception("Evaluation service error")
        
        contract_data = {
            'title': 'AI Failure Test Contract',
            'client': 'AI Failure Client',
            'text': 'Test contract for AI failure handling.',
            'signed': False
        }
        
        # Should still create contract but with fallback responses
        response = self.client.post('/api/contracts/', contract_data)
        
        # The view should handle the exception and provide fallback responses
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('contract_id', response.data)
        
        # Analysis should contain fallback message - check for actual error message format
        analysis_content = response.data.get('analysis', '')
        self.assertTrue(
            'Contract analysis temporarily unavailable' in analysis_content or
            'Contract analysis failed' in analysis_content,
            f"Expected fallback message not found in: {analysis_content}"
        )


if __name__ == '__main__':
    unittest.main() 