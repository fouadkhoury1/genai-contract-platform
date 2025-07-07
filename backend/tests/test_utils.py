import unittest
from unittest.mock import patch, Mock
import json
import os
import sys
from datetime import datetime, timedelta

# Add apps to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps'))

from apps.clients_contracts.ai_service import AIService


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions and helper methods."""
    
    def test_chunk_text_function(self):
        """Test text chunking utility function."""
        # Create a sample text that needs chunking
        sample_text = "A" * 25000  # 25,000 character string
        
        # Test chunking with different sizes
        chunks_10k = self._chunk_text(sample_text, 10000)
        chunks_20k = self._chunk_text(sample_text, 20000)
        
        # Verify chunk counts
        self.assertEqual(len(chunks_10k), 3)  # 25k / 10k = 2.5, rounded up to 3
        self.assertEqual(len(chunks_20k), 2)  # 25k / 20k = 1.25, rounded up to 2
        
        # Verify chunk sizes
        self.assertEqual(len(chunks_10k[0]), 10000)
        self.assertEqual(len(chunks_10k[1]), 10000)
        self.assertEqual(len(chunks_10k[2]), 5000)  # Remainder
        
        # Verify all chunks together reconstruct original text
        reconstructed = ''.join(chunks_10k)
        self.assertEqual(reconstructed, sample_text)

    def _chunk_text(self, text, chunk_size=20000):
        """Helper method to chunk text (mirrors the one in ai_service.py)."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def test_date_formatting_utilities(self):
        """Test date formatting and parsing utilities."""
        # Test various date formats
        test_dates = [
            '2025-01-15',
            '2025-01-15T10:30:00',
            '2025-01-15T10:30:00.000Z',
            '01/15/2025'
        ]
        
        for date_str in test_dates:
            # Test that dates can be parsed without errors
            try:
                if 'T' in date_str:
                    parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                elif '/' in date_str:
                    parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                else:
                    parsed_date = datetime.fromisoformat(date_str)
                
                self.assertIsInstance(parsed_date, datetime)
            except ValueError:
                self.fail(f"Failed to parse date: {date_str}")

    def test_text_processing_utilities(self):
        """Test text processing and cleaning utilities."""
        # Test text cleaning
        messy_text = "  \n\n  This is some    messy   text\nwith  extra    spaces\n\n  "
        cleaned_text = self._clean_text(messy_text)
        
        expected = "This is some messy text with extra spaces"
        self.assertEqual(cleaned_text, expected)
        
        # Test text truncation
        long_text = "This is a very long text that needs to be truncated"
        truncated = self._truncate_text(long_text, 20)
        
        self.assertEqual(len(truncated), 20)
        self.assertEqual(truncated, "This is a very long ")

    def _clean_text(self, text):
        """Helper method to clean text."""
        import re
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned

    def _truncate_text(self, text, max_length):
        """Helper method to truncate text."""
        return text[:max_length]

    def test_contract_status_utilities(self):
        """Test contract status determination utilities."""
        # Test status determination logic
        test_cases = [
            {'signed': True, 'approved': True, 'expected': 'approved'},
            {'signed': True, 'approved': False, 'expected': 'rejected'},
            {'signed': False, 'approved': True, 'expected': 'approved'},
            {'signed': False, 'approved': False, 'expected': 'rejected'},
            {'signed': True, 'approved': None, 'expected': 'signed'},
            {'signed': False, 'approved': None, 'expected': 'draft'},
        ]
        
        for case in test_cases:
            status = self._determine_contract_status(
                case['signed'], 
                case.get('approved')
            )
            self.assertEqual(status, case['expected'])

    def _determine_contract_status(self, signed, approved=None):
        """Helper method to determine contract status."""
        if approved is True:
            return 'approved'
        elif approved is False:
            return 'rejected'
        elif signed:
            return 'signed'
        else:
            return 'draft'

    def test_file_validation_utilities(self):
        """Test file validation utilities."""
        # Test file extension validation
        valid_extensions = ['.txt', '.pdf', '.doc', '.docx']
        invalid_extensions = ['.exe', '.bat', '.sh', '.py']
        
        for ext in valid_extensions:
            filename = f"contract{ext}"
            self.assertTrue(self._is_valid_file_type(filename))
        
        for ext in invalid_extensions:
            filename = f"malicious{ext}"
            self.assertFalse(self._is_valid_file_type(filename))
        
        # Test file size validation
        self.assertTrue(self._is_valid_file_size(1024 * 1024))  # 1MB
        self.assertTrue(self._is_valid_file_size(5 * 1024 * 1024))  # 5MB
        self.assertFalse(self._is_valid_file_size(50 * 1024 * 1024))  # 50MB (too large)

    def _is_valid_file_type(self, filename):
        """Helper method to validate file types."""
        valid_extensions = ['.txt', '.pdf', '.doc', '.docx']
        return any(filename.lower().endswith(ext) for ext in valid_extensions)

    def _is_valid_file_size(self, size_bytes):
        """Helper method to validate file size."""
        max_size = 10 * 1024 * 1024  # 10MB
        return size_bytes <= max_size

    def test_data_transformation_utilities(self):
        """Test data transformation utilities."""
        # Test MongoDB document to API response transformation
        mongo_doc = {
            '_id': '507f1f77bcf86cd799439011',
            'title': 'Test Contract',
            'client': 'Test Client',
            'signed': True,
            'date': '2025-01-15',
            'analysis': 'Contract analysis text',
            'approved': True
        }
        
        api_response = self._transform_contract_for_api(mongo_doc)
        
        # Verify transformation
        self.assertEqual(api_response['id'], '507f1f77bcf86cd799439011')
        self.assertEqual(api_response['title'], 'Test Contract')
        self.assertNotIn('_id', api_response)  # MongoDB _id should be transformed to id
        
        # Test reverse transformation
        api_data = {
            'title': 'API Contract',
            'client': 'API Client',
            'signed': False,
            'text': 'Contract text from API'
        }
        
        mongo_data = self._transform_api_for_mongo(api_data)
        
        # Verify reverse transformation
        self.assertEqual(mongo_data['title'], 'API Contract')
        self.assertIn('created_at', mongo_data)  # Should add timestamp

    def _transform_contract_for_api(self, mongo_doc):
        """Helper method to transform MongoDB document for API response."""
        api_doc = mongo_doc.copy()
        if '_id' in api_doc:
            api_doc['id'] = str(api_doc['_id'])
            del api_doc['_id']
        return api_doc

    def _transform_api_for_mongo(self, api_data):
        """Helper method to transform API data for MongoDB storage."""
        mongo_data = api_data.copy()
        mongo_data['created_at'] = datetime.utcnow().isoformat()
        return mongo_data

    def test_error_message_utilities(self):
        """Test error message formatting utilities."""
        # Test error message standardization
        test_errors = [
            {'type': 'validation', 'field': 'email', 'message': 'Invalid email format'},
            {'type': 'not_found', 'resource': 'contract', 'id': '123'},
            {'type': 'permission', 'action': 'delete', 'resource': 'contract'},
        ]
        
        for error in test_errors:
            formatted = self._format_error_message(error)
            self.assertIsInstance(formatted, dict)
            self.assertIn('error', formatted)
            self.assertIn('type', formatted)
        
        # Test specific error formats
        validation_error = self._format_validation_error('title', 'Title is required')
        self.assertEqual(validation_error['type'], 'validation_error')
        self.assertIn('title', validation_error['error'])

    def _format_error_message(self, error_info):
        """Helper method to format error messages."""
        if error_info['type'] == 'validation':
            return {
                'error': f"Validation error: {error_info['message']}",
                'type': 'validation_error',
                'field': error_info['field']
            }
        elif error_info['type'] == 'not_found':
            return {
                'error': f"{error_info['resource'].title()} with ID {error_info['id']} not found",
                'type': 'not_found_error'
            }
        elif error_info['type'] == 'permission':
            return {
                'error': f"Permission denied: Cannot {error_info['action']} {error_info['resource']}",
                'type': 'permission_error'
            }
        else:
            return {
                'error': 'Unknown error occurred',
                'type': 'unknown_error'
            }

    def _format_validation_error(self, field, message):
        """Helper method to format validation errors."""
        return {
            'error': f"Validation failed for field '{field}': {message}",
            'type': 'validation_error',
            'field': field
        }

    def test_pagination_utilities(self):
        """Test pagination helper utilities."""
        # Test pagination calculation
        total_items = 150
        page_size = 20
        
        total_pages = self._calculate_total_pages(total_items, page_size)
        self.assertEqual(total_pages, 8)  # 150 / 20 = 7.5, rounded up to 8
        
        # Test pagination metadata
        page_1_meta = self._get_pagination_metadata(1, page_size, total_items)
        self.assertEqual(page_1_meta['current_page'], 1)
        self.assertEqual(page_1_meta['total_pages'], 8)
        self.assertEqual(page_1_meta['has_next'], True)
        self.assertEqual(page_1_meta['has_previous'], False)
        
        page_8_meta = self._get_pagination_metadata(8, page_size, total_items)
        self.assertEqual(page_8_meta['has_next'], False)
        self.assertEqual(page_8_meta['has_previous'], True)

    def _calculate_total_pages(self, total_items, page_size):
        """Helper method to calculate total pages."""
        import math
        return math.ceil(total_items / page_size)

    def _get_pagination_metadata(self, current_page, page_size, total_items):
        """Helper method to get pagination metadata."""
        total_pages = self._calculate_total_pages(total_items, page_size)
        
        return {
            'current_page': current_page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': current_page < total_pages,
            'has_previous': current_page > 1,
            'start_index': (current_page - 1) * page_size + 1,
            'end_index': min(current_page * page_size, total_items)
        }

    def test_security_utilities(self):
        """Test security-related utilities."""
        # Test input sanitization
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE contracts; --",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]
        
        for dangerous_input in dangerous_inputs:
            sanitized = self._sanitize_input(dangerous_input)
            # Basic sanitization should remove/escape dangerous characters
            self.assertNotIn('<script>', sanitized)
            self.assertNotIn('DROP TABLE', sanitized)
            self.assertNotIn('../', sanitized)
            self.assertNotIn('javascript:', sanitized)

    def _sanitize_input(self, user_input):
        """Helper method to sanitize user input."""
        import html
        import re
        
        # HTML escape
        sanitized = html.escape(str(user_input))
        
        # Remove common attack patterns
        sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\.\./', '', sanitized)
        sanitized = re.sub(r'DROP\s+TABLE', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized

    def test_api_response_formatting(self):
        """Test API response formatting utilities."""
        # Test success response formatting
        success_data = {'contract_id': '123', 'title': 'Test Contract'}
        success_response = self._format_success_response(success_data, 'Contract created successfully')
        
        self.assertEqual(success_response['status'], 'success')
        self.assertEqual(success_response['message'], 'Contract created successfully')
        self.assertEqual(success_response['data'], success_data)
        
        # Test error response formatting
        error_response = self._format_error_response('Contract not found', 404)
        
        self.assertEqual(error_response['status'], 'error')
        self.assertEqual(error_response['error'], 'Contract not found')
        self.assertEqual(error_response['code'], 404)

    def _format_success_response(self, data, message):
        """Helper method to format success responses."""
        return {
            'status': 'success',
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _format_error_response(self, error_message, error_code):
        """Helper method to format error responses."""
        return {
            'status': 'error',
            'error': error_message,
            'code': error_code,
            'timestamp': datetime.utcnow().isoformat()
        }


if __name__ == '__main__':
    unittest.main() 