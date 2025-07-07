import unittest
from unittest.mock import patch, Mock, MagicMock
import json
import os
import sys

# Add apps to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps'))

from apps.clients_contracts.ai_service import AIService


class TestAIService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_contract_text = """
        PURCHASE AGREEMENT
        
        This agreement is between Buyer and Seller for the purchase of property.
        
        PAYMENT TERMS:
        - 20% deposit due upon signing
        - Balance due at closing
        
        TERMINATION:
        Either party may terminate with 30 days notice.
        
        CONFIDENTIALITY:
        All information shall remain confidential.
        """
        
        self.mock_deepseek_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is a well-structured purchase agreement with clear payment terms."
                    }
                }
            ]
        }
        
        self.mock_evaluation_response = {
            "choices": [
                {
                    "message": {
                        "content": "The contract is approved with clear terms and conditions."
                    }
                }
            ]
        }
        
        self.mock_clauses_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps([
                            {
                                "type": "Payment Terms",
                                "content": "20% deposit due upon signing, balance due at closing",
                                "risk_level": "low",
                                "obligations": ["Make deposit payment", "Pay balance at closing"]
                            },
                            {
                                "type": "Termination",
                                "content": "Either party may terminate with 30 days notice",
                                "risk_level": "medium",
                                "obligations": ["Provide 30 days notice"]
                            }
                        ])
                    }
                }
            ]
        }

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.clients_contracts.ai_service.session.post')
    def test_analyze_contract_success(self, mock_post):
        """Test successful contract analysis."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_deepseek_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = AIService.analyze_contract(self.sample_contract_text)
        
        self.assertIn('analysis', result)
        self.assertIn('model_used', result)
        self.assertEqual(result['analysis'], "This is a well-structured purchase agreement with clear payment terms.")
        self.assertEqual(result['model_used'], "DeepSeek Reasoning Model (Live)")
        mock_post.assert_called_once()

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.clients_contracts.ai_service.session.post')
    def test_analyze_contract_timeout(self, mock_post):
        """Test contract analysis with timeout."""
        mock_post.side_effect = Exception("Request timed out")
        
        result = AIService.analyze_contract(self.sample_contract_text)
        
        self.assertIn('analysis', result)
        self.assertIn('model_used', result)
        self.assertEqual(result['model_used'], "Fallback Response")
        self.assertIn("Contract analysis failed", result['analysis'])

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.clients_contracts.ai_service.session.post')
    def test_evaluate_contract_approved(self, mock_post):
        """Test contract evaluation - approved."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_evaluation_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = AIService.evaluate_contract(self.sample_contract_text)
        
        self.assertIn('approved', result)
        self.assertIn('reasoning', result)
        self.assertTrue(result['approved'])  # "approved" in response means approved=True
        self.assertEqual(result['reasoning'], "The contract is approved with clear terms and conditions.")

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.clients_contracts.ai_service.session.post')
    def test_evaluate_contract_not_approved(self, mock_post):
        """Test contract evaluation - not approved."""
        mock_not_approved_response = {
            "choices": [
                {
                    "message": {
                        "content": "The contract is not approved due to unclear payment terms."
                    }
                }
            ]
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_not_approved_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = AIService.evaluate_contract(self.sample_contract_text)
        
        self.assertIn('approved', result)
        self.assertIn('reasoning', result)
        self.assertFalse(result['approved'])  # "not approved" in response means approved=False

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.clients_contracts.ai_service.session.post')
    def test_extract_clauses_success(self, mock_post):
        """Test successful clause extraction."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_clauses_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = AIService.extract_clauses(self.sample_contract_text)
        
        self.assertIn('clauses', result)
        self.assertIn('clause_count', result)
        self.assertIn('model_used', result)
        self.assertEqual(len(result['clauses']), 2)
        self.assertEqual(result['clause_count'], 2)
        self.assertEqual(result['model_used'], "deepseek-chat")
        
        # Check first clause
        first_clause = result['clauses'][0]
        self.assertEqual(first_clause['type'], "Payment Terms")
        self.assertEqual(first_clause['risk_level'], "low")
        self.assertIn("obligations", first_clause)

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.clients_contracts.ai_service.session.post')
    def test_extract_clauses_invalid_json(self, mock_post):
        """Test clause extraction with invalid JSON response."""
        mock_invalid_response = {
            "choices": [
                {
                    "message": {
                        "content": "Invalid JSON response from AI"
                    }
                }
            ]
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_invalid_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = AIService.extract_clauses(self.sample_contract_text)
        
        self.assertIn('clauses', result)
        self.assertIn('clause_count', result)
        self.assertIn('error', result)
        self.assertEqual(len(result['clauses']), 0)
        self.assertEqual(result['clause_count'], 0)
        self.assertIn("Failed to parse AI response as JSON", result['error'])

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.clients_contracts.ai_service.session.post')
    def test_extract_clauses_chunked_text(self, mock_post):
        """Test clause extraction with large text that requires chunking."""
        # Create a large contract text (>50000 chars)
        large_contract_text = self.sample_contract_text * 1000
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_clauses_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = AIService.extract_clauses(large_contract_text)
        
        self.assertIn('clauses', result)
        self.assertIn('clause_count', result)
        self.assertIn('model_used', result)
        # Should have been called multiple times for chunks
        self.assertGreater(mock_post.call_count, 1)

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    def test_test_api_connection_success(self):
        """Test API connection test - success."""
        with patch('apps.clients_contracts.ai_service.session.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = AIService.test_api_connection()
            
            self.assertTrue(result)

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key'})
    def test_test_api_connection_failure(self):
        """Test API connection test - failure."""
        with patch('apps.clients_contracts.ai_service.session.post') as mock_post:
            mock_post.side_effect = Exception("Connection failed")
            
            result = AIService.test_api_connection()
            
            self.assertFalse(result)

    def test_missing_api_key(self):
        """Test behavior when DEEPSEEK_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear the DEEPSEEK_API_KEY to simulate missing key
            if 'DEEPSEEK_API_KEY' in os.environ:
                del os.environ['DEEPSEEK_API_KEY']
            
            # Mock the session.post to simulate what happens when no API key
            with patch('apps.clients_contracts.ai_service.session.post') as mock_post:
                mock_post.side_effect = Exception("API key not provided")
                
                result = AIService.test_api_connection()
                self.assertFalse(result)


if __name__ == '__main__':
    unittest.main() 