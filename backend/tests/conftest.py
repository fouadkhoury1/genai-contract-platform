import pytest
import os
import sys
from unittest.mock import patch
from django.test import override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Add apps to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps'))

from apps.clients_contracts.views import contracts_collection, clients_collection


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Configure the Django database for testing.
    """
    settings = {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
    }
    with override_settings(**settings):
        yield


@pytest.fixture
def api_client():
    """
    Provide a DRF API client for testing.
    """
    return APIClient()


@pytest.fixture
def test_user(db):
    """
    Create a test user for authentication.
    """
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, test_user):
    """
    Provide an authenticated API client.
    """
    refresh = RefreshToken.for_user(test_user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    return api_client


@pytest.fixture
def sample_contract_data():
    """
    Provide sample contract data for testing.
    """
    return {
        'title': 'Test Contract',
        'client': 'Test Client Corp',
        'signed': False,
        'text': 'This is a sample contract text with payment terms and conditions.',
        'date': '2025-01-15'
    }


@pytest.fixture
def sample_client_data():
    """
    Provide sample client data for testing.
    """
    return {
        'name': 'Test Client Corp',
        'email': 'client@testcorp.com',
        'company_id': 'TC001',
        'active': True
    }


@pytest.fixture
def mock_ai_responses():
    """
    Provide mock AI service responses for consistent testing.
    """
    return {
        'analysis': {
            'analysis': 'This is a comprehensive contract analysis.',
            'model_used': 'DeepSeek Reasoning Model (Live)'
        },
        'evaluation': {
            'approved': True,
            'reasoning': 'Contract meets all requirements.'
        },
        'clauses': {
            'clauses': [
                {
                    'type': 'Payment Terms',
                    'content': 'Payment due within 30 days',
                    'risk_level': 'low',
                    'obligations': ['Make payment on time']
                },
                {
                    'type': 'Termination',
                    'content': 'Either party may terminate with notice',
                    'risk_level': 'medium',
                    'obligations': ['Provide written notice']
                }
            ],
            'clause_count': 2,
            'model_used': 'deepseek-chat'
        }
    }


@pytest.fixture
def mock_ai_service(mock_ai_responses):
    """
    Mock the AI service methods for testing.
    """
    with patch('apps.clients_contracts.ai_service.AIService.analyze_contract') as mock_analyze, \
         patch('apps.clients_contracts.ai_service.AIService.evaluate_contract') as mock_evaluate, \
         patch('apps.clients_contracts.ai_service.AIService.extract_clauses') as mock_extract:
        
        mock_analyze.return_value = mock_ai_responses['analysis']
        mock_evaluate.return_value = mock_ai_responses['evaluation']
        mock_extract.return_value = mock_ai_responses['clauses']
        
        yield {
            'analyze': mock_analyze,
            'evaluate': mock_evaluate,
            'extract': mock_extract
        }


@pytest.fixture
def clean_mongodb():
    """
    Clean MongoDB collections before and after tests.
    """
    # Clean before test
    try:
        contracts_collection.delete_many({})
        clients_collection.delete_many({})
    except:
        pass
    
    yield
    
    # Clean after test
    try:
        contracts_collection.delete_many({})
        clients_collection.delete_many({})
    except:
        pass


@pytest.fixture
def sample_contract_in_db(clean_mongodb):
    """
    Insert a sample contract into MongoDB for testing.
    """
    contract_data = {
        'title': 'Database Test Contract',
        'client': 'Database Test Client',
        'signed': True,
        'text': 'Sample contract text in database.',
        'date': '2025-01-15',
        'analysis': 'Sample analysis result',
        'approved': True
    }
    
    result = contracts_collection.insert_one(contract_data)
    contract_data['_id'] = result.inserted_id
    return contract_data


@pytest.fixture
def sample_client_in_db(clean_mongodb):
    """
    Insert a sample client into MongoDB for testing.
    """
    client_data = {
        'name': 'Database Test Client',
        'email': 'dbtest@client.com',
        'company_id': 'DTC001',
        'active': True
    }
    
    result = clients_collection.insert_one(client_data)
    client_data['_id'] = result.inserted_id
    return client_data


@pytest.fixture(scope='session')
def test_settings():
    """
    Override Django settings for testing.
    """
    settings = {
        'SECRET_KEY': 'test-secret-key-for-testing-only',
        'DEBUG': True,
        'ALLOWED_HOSTS': ['testserver'],
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        'CACHES': {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
        'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
        'PASSWORD_HASHERS': [
            'django.contrib.auth.hashers.MD5PasswordHasher',  # Fast for testing
        ],
        'CELERY_TASK_ALWAYS_EAGER': True,  # Execute tasks synchronously
        'CELERY_TASK_EAGER_PROPAGATES': True,
    }
    
    with override_settings(**settings):
        yield


@pytest.fixture
def mock_file_upload():
    """
    Provide mock file upload objects for testing.
    """
    import io
    
    def create_mock_file(content, filename):
        file_obj = io.BytesIO(content.encode() if isinstance(content, str) else content)
        file_obj.name = filename
        return file_obj
    
    return create_mock_file


@pytest.fixture
def environment_variables():
    """
    Mock environment variables for testing.
    """
    env_vars = {
        'DEEPSEEK_API_KEY': 'test-deepseek-api-key',
        'DJANGO_SECRET_KEY': 'test-django-secret-key',
        'DEBUG': 'True',
        'MONGO_URI': 'mongodb://localhost:27017/test_contract_platform'
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest settings.
    """
    import django
    from django.conf import settings
    
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'rest_framework',
                'rest_framework_simplejwt',
                'apps.authentication',
                'apps.clients_contracts',
            ],
            SECRET_KEY='test-secret-key',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            REST_FRAMEWORK={
                'DEFAULT_AUTHENTICATION_CLASSES': [
                    'rest_framework_simplejwt.authentication.JWTAuthentication',
                ],
                'DEFAULT_PERMISSION_CLASSES': [
                    'rest_framework.permissions.IsAuthenticated',
                ],
            },
            USE_TZ=True,
        )
    
    django.setup()


# Custom pytest markers
def pytest_collection_modifyitems(config, items):
    """
    Add custom markers to tests.
    """
    for item in items:
        # Mark tests that require database
        if 'db' in item.fixturenames:
            item.add_marker(pytest.mark.django_db)
        
        # Mark integration tests
        if 'integration' in item.module.__name__:
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if 'slow' in item.name or 'integration' in item.name:
            item.add_marker(pytest.mark.slow)


# Test discovery configuration
collect_ignore_glob = [
    "*migrations*",
    "*venv*",
    "*node_modules*",
] 