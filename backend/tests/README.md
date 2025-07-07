# Test Suite for GenAI Contract Platform

This directory contains comprehensive unit and integration tests for the GenAI Contract Platform backend.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── pytest.ini                 # Pytest settings and markers
├── README.md                   # This file
├── test_ai_service.py          # AI service unit tests
├── test_authentication.py     # Authentication unit tests
├── test_integration.py         # End-to-end integration tests
├── test_utils.py              # Utility function tests
└── test_views.py              # API endpoint integration tests
```

## Test Categories

### Unit Tests
- **test_ai_service.py**: Tests for AI analysis, evaluation, and clause extraction
- **test_authentication.py**: Tests for user registration, login, JWT tokens
- **test_utils.py**: Tests for utility functions, data transformation, validation

### Integration Tests
- **test_views.py**: Tests for all API endpoints with database integration
- **test_integration.py**: End-to-end workflow tests

## Running Tests

### Prerequisites
1. Ensure you're in the backend directory
2. Activate your virtual environment
3. Install test dependencies:
   ```bash
   pip install pytest pytest-django pytest-cov
   ```

### Run All Tests
```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=apps --cov-report=html
```

### Run Specific Test Categories
```bash
# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Run only AI service tests
python -m pytest -m ai_service

# Run only authentication tests
python -m pytest -m auth
```

### Run Specific Test Files
```bash
# Run AI service tests
python -m pytest tests/test_ai_service.py

# Run authentication tests
python -m pytest tests/test_authentication.py

# Run integration tests
python -m pytest tests/test_integration.py
```

### Run with Different Verbosity
```bash
# Quiet output
python -m pytest -q

# Verbose output
python -m pytest -v

# Very verbose output
python -m pytest -vv
```

## Test Markers

The test suite uses custom markers to categorize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.django_db` - Tests requiring database
- `@pytest.mark.ai_service` - Tests mocking AI service
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.contracts` - Contract management tests
- `@pytest.mark.clients` - Client management tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.utils` - Utility function tests

## Test Coverage

The test suite aims for 80%+ code coverage. Generate coverage reports with:

```bash
python -m pytest --cov=apps --cov-report=html
```

View the HTML coverage report by opening `htmlcov/index.html` in your browser.

## Test Files Description

### test_ai_service.py
Tests the AI service integration including:
- Contract analysis with DeepSeek API
- Contract evaluation and approval logic
- Clause extraction and classification
- Error handling for API failures
- Chunked processing for large contracts

**Key Test Cases:**
- Successful AI analysis
- API timeout handling
- Invalid JSON response handling
- Large contract chunking
- Missing API key scenarios

### test_authentication.py
Tests authentication and authorization:
- User registration and validation
- Login with username/password
- JWT token generation and validation
- Protected endpoint access
- Token refresh functionality
- Password strength validation

**Key Test Cases:**
- Successful registration/login
- Invalid credentials handling
- Token expiration
- Concurrent sessions
- Password validation

### test_views.py
Tests all API endpoints with database integration:
- Contract CRUD operations
- Client management
- Authentication endpoints
- Analysis and clause extraction endpoints
- Error handling and validation

**Key Test Cases:**
- Contract upload and analysis
- File upload processing
- Contract reanalysis
- Client-contract relationships
- Authentication required checks

### test_integration.py
End-to-end workflow tests:
- Complete contract upload and analysis workflow
- Contract reanalysis with new files
- Client and contract relationship management
- Authentication integration
- Error handling across the system

**Key Test Cases:**
- Full contract lifecycle
- Multi-step workflows
- Cross-system integration
- Error propagation

### test_utils.py
Tests utility functions and helpers:
- Text processing and cleaning
- Data transformation (MongoDB ↔ API)
- File validation
- Error message formatting
- Pagination utilities
- Security functions

**Key Test Cases:**
- Text chunking algorithms
- Date formatting
- File type validation
- Data sanitization
- Status determination

## Environment Setup for Testing

### Environment Variables
Tests use mocked environment variables. The following are automatically set:
- `DEEPSEEK_API_KEY`: Mock API key
- `DJANGO_SECRET_KEY`: Test secret key
- `DEBUG`: True
- `MONGO_URI`: Test database URI

### Database Configuration
- Tests use SQLite in-memory database for Django models
- MongoDB operations are mocked or use test collections
- Database is automatically cleaned between tests

### AI Service Mocking
AI service calls are mocked by default to:
- Ensure consistent test results
- Avoid external API dependencies
- Speed up test execution
- Test error scenarios

## Writing New Tests

### Test Structure
Follow this structure for new tests:

```python
import unittest
from unittest.mock import patch, Mock
# ... other imports

class TestYourFeature(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Test setup code
        
    def test_your_feature_success(self):
        """Test successful operation."""
        # Test implementation
        
    def test_your_feature_error(self):
        """Test error handling."""
        # Error test implementation
```

### Fixtures and Mocks
Use the fixtures in `conftest.py`:
- `authenticated_client` - API client with JWT token
- `sample_contract_data` - Sample contract data
- `mock_ai_service` - Mocked AI service responses
- `clean_mongodb` - Clean MongoDB before/after

### Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

## Continuous Integration

This test suite is designed to run in CI/CD environments:
- All external dependencies are mocked
- Tests are deterministic and repeatable
- Coverage thresholds are enforced
- Test results are available in multiple formats

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the virtual environment is activated and dependencies are installed
2. **Database Errors**: Tests use in-memory databases, no setup required
3. **MongoDB Errors**: MongoDB operations are mocked, check mock setup
4. **AI Service Errors**: AI calls are mocked, verify mock configurations

### Debug Mode
Run tests with debug information:
```bash
python -m pytest --pdb  # Drop into debugger on failure
python -m pytest -s    # Don't capture output
python -m pytest --lf   # Run only last failed tests
```

## Contributing

When adding new features:
1. Write tests before implementing features (TDD)
2. Ensure tests are comprehensive and cover edge cases
3. Maintain or improve code coverage
4. Add appropriate test markers
5. Update this README if adding new test categories

For questions about the test suite, refer to the test files or create an issue in the project repository. 