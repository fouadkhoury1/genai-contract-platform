# GenAI Contract Platform API Documentation

## Overview

The GenAI Contract Platform API provides endpoints for managing contracts, clients, and AI-powered contract analysis. This RESTful API supports contract upload, analysis, clause extraction, and comprehensive contract management workflows.

**Base URL:** `http://localhost:8000/api`

**Version:** 1.0

## Authentication

The API uses JWT (JSON Web Token) authentication. All protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow

1. **Register** a new user or **Login** with existing credentials
2. Include the returned token in subsequent requests
3. Token format: `Bearer <your-jwt-token>`

### Headers Required for Protected Endpoints

```http
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

---

## Endpoints

### Authentication Endpoints

#### POST /auth/register/
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (201 Created):**
```json
{
  "message": "User registered successfully."
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Username already exists"
}
```

#### POST /auth/login/
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "john_doe"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Invalid credentials"
}
```

---

### Contract Management

#### POST /contracts/
Create a new contract with optional file upload and automatic AI analysis.

**Headers:**
```http
Authorization: Bearer <token>
Content-Type: multipart/form-data  // For file uploads
Content-Type: application/json     // For text-only contracts
```

**Request Body (JSON):**
```json
{
  "title": "Service Agreement 2025",
  "client": "Acme Corporation", 
  "signed": false,
  "text": "This is the contract text content...",
  "date": "2025-01-15"
}
```

**Request Body (File Upload):**
```form-data
title: "Service Agreement 2025"
client: "Acme Corporation"
signed: false
file: <contract.pdf>
date: "2025-01-15"
```

**Response (201 Created):**
```json
{
  "contract_id": "60f7b3c4e1b2c3d4e5f6g7h8",
  "title": "Service Agreement 2025",
  "client": "Acme Corporation",
  "signed": false,
  "date": "2025-01-15",
  "analysis": "This contract demonstrates strong legal framework with clear payment terms...",
  "approved": true,
  "evaluation_reasoning": "Contract meets all compliance requirements and business criteria.",
  "model_used": "DeepSeek Reasoning Model (Live)",
  "analysis_date": "2025-01-15T10:30:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Missing required field: title"
}
```

#### GET /contracts/
Retrieve all contracts for the authenticated user.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "_id": "60f7b3c4e1b2c3d4e5f6g7h8",
    "title": "Service Agreement 2025",
    "client": "Acme Corporation",
    "signed": false,
    "date": "2025-01-15",
    "analysis": "Contract analysis...",
    "approved": true,
    "created_at": "2025-01-15T09:00:00Z"
  },
  {
    "_id": "60f7b3c4e1b2c3d4e5f6g7h9",
    "title": "NDA Agreement",
    "client": "Tech Solutions Inc",
    "signed": true,
    "date": "2025-01-10",
    "analysis": "Standard NDA with appropriate clauses...",
    "approved": true,
    "created_at": "2025-01-10T14:20:00Z"
  }
]
```

#### GET /contracts/{id}/
Retrieve a specific contract by ID.

**Parameters:**
- `id` (string): Contract ObjectId

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "_id": "60f7b3c4e1b2c3d4e5f6g7h8",
  "title": "Service Agreement 2025",
  "client": "Acme Corporation",
  "signed": false,
  "date": "2025-01-15",
  "text": "Full contract text content...",
  "analysis": "Comprehensive analysis...",
  "approved": true,
  "evaluation_reasoning": "Contract meets requirements...",
  "clauses": ["Payment Terms", "Termination", "Confidentiality"],
  "clause_count": 3,
  "model_used": "DeepSeek Reasoning Model (Live)",
  "analysis_date": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-15T09:00:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Contract not found"
}
```

#### PUT /contracts/{id}/
Update an existing contract.

**Parameters:**
- `id` (string): Contract ObjectId

**Headers:**
```http
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Updated Service Agreement 2025",
  "signed": true,
  "client": "Acme Corporation Ltd"
}
```

**Response (200 OK):**
```json
{
  "_id": "60f7b3c4e1b2c3d4e5f6g7h8",
  "title": "Updated Service Agreement 2025",
  "client": "Acme Corporation Ltd",
  "signed": true,
  "date": "2025-01-15",
  "updated_at": "2025-01-15T15:45:00Z"
}
```

#### DELETE /contracts/{id}/
Delete a contract.

**Parameters:**
- `id` (string): Contract ObjectId

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "message": "Contract deleted successfully"
}
```

---

### AI Analysis Endpoints

#### GET /contracts/{id}/analysis/
Retrieve detailed analysis for a specific contract.

**Parameters:**
- `id` (string): Contract ObjectId

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "analysis": "## Contract Analysis\n\n**Overview:** This service agreement demonstrates a well-structured legal framework...\n\n**Key Findings:**\n- Clear payment terms with 30-day payment window\n- Comprehensive termination clauses\n- Strong confidentiality provisions...",
  "model_used": "DeepSeek Reasoning Model (Live)",
  "analysis_date": "2025-01-15T10:30:00Z",
  "contract_title": "Service Agreement 2025",
  "contract_client": "Acme Corporation"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Analysis not found for this contract"
}
```

#### POST /contracts/{id}/clauses/
Extract and classify clauses from a contract.

**Parameters:**
- `id` (string): Contract ObjectId

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "clauses": [
    {
      "type": "Payment Terms",
      "content": "Payment shall be made within 30 days of invoice receipt. Late payments may incur a 1.5% monthly fee.",
      "risk_level": "low",
      "obligations": [
        "Make payment within 30 days",
        "Pay late fees if applicable"
      ]
    },
    {
      "type": "Termination",
      "content": "Either party may terminate this agreement with 60 days written notice.",
      "risk_level": "medium", 
      "obligations": [
        "Provide 60 days written notice",
        "Complete ongoing obligations"
      ]
    },
    {
      "type": "Confidentiality",
      "content": "All proprietary information shared must remain confidential for 5 years post-termination.",
      "risk_level": "high",
      "obligations": [
        "Maintain confidentiality",
        "Return confidential materials",
        "Comply with 5-year restriction"
      ]
    }
  ],
  "clause_count": 3,
  "model_used": "deepseek-chat",
  "extraction_date": "2025-01-15T11:00:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "No contract text available for clause extraction"
}
```

#### POST /contracts/{id}/reanalyze/
Reanalyze a contract with a new file upload.

**Parameters:**
- `id` (string): Contract ObjectId

**Headers:**
```http
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body:**
```form-data
title: "Updated Service Agreement 2025"
file: <updated_contract.pdf>
```

**Response (200 OK):**
```json
{
  "contract_id": "60f7b3c4e1b2c3d4e5f6g7h8",
  "title": "Updated Service Agreement 2025",
  "analysis": "Updated analysis shows improved terms and conditions...",
  "approved": true,
  "evaluation_reasoning": "Updated contract addresses previous concerns...",
  "model_used": "DeepSeek Reasoning Model (Live)",
  "analysis_date": "2025-01-15T16:20:00Z"
}
```

---

### Client Management

#### POST /clients/
Create a new client.

**Headers:**
```http
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "email": "contact@acme.com",
  "company_id": "ACME001",
  "active": true
}
```

**Response (201 Created):**
```json
{
  "_id": "60f7b3c4e1b2c3d4e5f6g7h8",
  "name": "Acme Corporation", 
  "email": "contact@acme.com",
  "company_id": "ACME001",
  "active": true,
  "created_at": "2025-01-15T09:00:00Z"
}
```

#### GET /clients/
Retrieve all clients.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "_id": "60f7b3c4e1b2c3d4e5f6g7h8",
    "name": "Acme Corporation",
    "email": "contact@acme.com", 
    "company_id": "ACME001",
    "active": true,
    "created_at": "2025-01-15T09:00:00Z"
  },
  {
    "_id": "60f7b3c4e1b2c3d4e5f6g7h9", 
    "name": "Tech Solutions Inc",
    "email": "info@techsolutions.com",
    "company_id": "TECH002",
    "active": true,
    "created_at": "2025-01-10T14:30:00Z"
  }
]
```

#### GET /clients/{id}/contracts/
Retrieve all contracts for a specific client.

**Parameters:**
- `id` (string): Client ObjectId

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "_id": "60f7b3c4e1b2c3d4e5f6g7h8",
    "title": "Service Agreement 2025",
    "client": "Acme Corporation",
    "signed": false,
    "date": "2025-01-15",
    "approved": true
  },
  {
    "_id": "60f7b3c4e1b2c3d4e5f6g7h9",
    "title": "NDA Agreement",
    "client": "Acme Corporation", 
    "signed": true,
    "date": "2025-01-10",
    "approved": true
  }
]
```

---

### System Monitoring

#### GET /healthz/
Health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T12:00:00Z",
  "version": "1.0.0"
}
```

#### GET /readyz/
Readiness check endpoint.

**Response (200 OK):**
```json
{
  "status": "ready",
  "database": "connected",
  "ai_service": "available",
  "timestamp": "2025-01-15T12:00:00Z"
}
```

#### GET /metrics/
System metrics endpoint.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "request_count": 1250,
  "average_latency": 145.7,
  "active_users": 12,
  "contracts_processed": 89,
  "success_rate": 98.4,
  "timestamp": "2025-01-15T12:00:00Z"
}
```

#### GET /logs/
System logs endpoint.

**Headers:**
```http
Authorization: Bearer <token>
```

**Query Parameters:**
- `level` (optional): Log level filter (info, warning, error)
- `limit` (optional): Number of log entries (default: 100)

**Response (200 OK):**
```json
{
  "results": [
    {
      "timestamp": "2025-01-15T11:58:32Z",
      "level": "info",
      "message": "Contract analysis completed successfully",
      "contract_id": "60f7b3c4e1b2c3d4e5f6g7h8"
    },
    {
      "timestamp": "2025-01-15T11:57:15Z", 
      "level": "warning",
      "message": "AI service response time exceeded threshold",
      "duration": 8.5
    }
  ],
  "total": 245,
  "page": 1
}
```

---

## Error Handling

### Standard HTTP Status Codes

- **200 OK** - Request successful
- **201 Created** - Resource created successfully  
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Authentication required or invalid
- **403 Forbidden** - Access denied
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

### Error Response Format

All error responses follow this structure:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-15T12:00:00Z",
  "details": {
    "field": "Additional error details if applicable"
  }
}
```

### Common Error Scenarios

#### Authentication Errors
```json
{
  "error": "Authentication token required",
  "code": "AUTH_TOKEN_MISSING"
}
```

```json
{
  "error": "Invalid or expired token",
  "code": "AUTH_TOKEN_INVALID"
}
```

#### Validation Errors
```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "title": "Title is required",
    "client": "Client name must be provided"
  }
}
```

#### AI Service Errors
```json
{
  "error": "Contract analysis temporarily unavailable due to connection issues. Please try again later.",
  "code": "AI_SERVICE_UNAVAILABLE"
}
```

---

## Usage Examples

### Complete Contract Upload and Analysis Workflow

```bash
# 1. Register/Login to get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password"
  }'

# Response: {"token": "eyJhbGciOiJIUzI1NiIs...", "user": {...}}

# 2. Upload contract with file
curl -X POST http://localhost:8000/api/contracts/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -F "title=Service Agreement 2025" \
  -F "client=Acme Corporation" \
  -F "signed=false" \
  -F "file=@contract.pdf"

# Response: {"contract_id": "60f7b3c4...", "analysis": "...", "approved": true}

# 3. Extract clauses from the contract
curl -X POST http://localhost:8000/api/contracts/60f7b3c4e1b2c3d4e5f6g7h8/clauses/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Response: {"clauses": [...], "clause_count": 3}

# 4. Get detailed analysis
curl -X GET http://localhost:8000/api/contracts/60f7b3c4e1b2c3d4e5f6g7h8/analysis/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Response: {"analysis": "## Contract Analysis...", "model_used": "..."}
```

### Client and Contract Management

```bash
# Create a new client
curl -X POST http://localhost:8000/api/clients/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Solutions Inc",
    "email": "contact@techsolutions.com",
    "company_id": "TECH001"
  }'

# Get all contracts for a client
curl -X GET http://localhost:8000/api/clients/60f7b3c4e1b2c3d4e5f6g7h8/contracts/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Update contract status
curl -X PUT http://localhost:8000/api/contracts/60f7b3c4e1b2c3d4e5f6g7h8/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "signed": true,
    "title": "Updated Service Agreement 2025"
  }'
```

---

## Rate Limiting

- **Authentication endpoints**: 10 requests per minute per IP
- **Contract operations**: 100 requests per hour per user
- **AI analysis operations**: 20 requests per hour per user
- **System monitoring**: 60 requests per minute per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1642694400
```

---

## Data Types and Formats

### Contract Object
```typescript
{
  _id: string,                    // MongoDB ObjectId
  title: string,                  // Contract title
  client?: string,                // Client name (optional)
  signed: boolean,                // Signature status
  date?: string,                  // ISO date string (YYYY-MM-DD)
  text?: string,                  // Full contract text
  analysis?: string,              // AI analysis result (markdown)
  approved?: boolean,             // AI approval status
  evaluation_reasoning?: string,  // AI evaluation explanation
  clauses?: string[],            // Extracted clause types
  clause_count?: number,         // Number of clauses
  model_used?: string,           // AI model identifier
  analysis_date?: string,        // ISO datetime string
  created_at: string,            // ISO datetime string
  updated_at?: string            // ISO datetime string
}
```

### Client Object
```typescript
{
  _id: string,           // MongoDB ObjectId
  name: string,          // Client company name
  email?: string,        // Contact email
  company_id?: string,   // Internal company identifier
  active: boolean,       // Active status
  created_at: string     // ISO datetime string
}
```

### Clause Object
```typescript
{
  type: string,              // Clause category (e.g., "Payment Terms")
  content: string,           // Full clause text
  risk_level: string,        // "low" | "medium" | "high"
  obligations: string[]      // List of obligations
}
```

---

## SDK and Integration

### JavaScript/Node.js Example

```javascript
class ContractPlatformAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async uploadContract(contractData, file) {
    const formData = new FormData();
    formData.append('title', contractData.title);
    formData.append('client', contractData.client);
    formData.append('signed', contractData.signed);
    if (file) formData.append('file', file);

    const response = await fetch(`${this.baseURL}/contracts/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });

    return response.json();
  }

  async getContracts() {
    const response = await fetch(`${this.baseURL}/contracts/`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });

    return response.json();
  }

  async extractClauses(contractId) {
    const response = await fetch(`${this.baseURL}/contracts/${contractId}/clauses/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });

    return response.json();
  }
}

// Usage
const api = new ContractPlatformAPI('http://localhost:8000/api', 'your-jwt-token');

// Upload contract
const result = await api.uploadContract({
  title: 'Service Agreement',
  client: 'Acme Corp',
  signed: false
}, fileObject);

console.log('Contract uploaded:', result.contract_id);
console.log('Analysis:', result.analysis);
console.log('Approved:', result.approved);
```

### Python Example

```python
import requests
import json

class ContractPlatformAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def upload_contract(self, title, client, signed=False, file_path=None, text=None):
        url = f"{self.base_url}/contracts/"
        
        if file_path:
            files = {'file': open(file_path, 'rb')}
            data = {
                'title': title,
                'client': client,
                'signed': str(signed).lower()
            }
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.post(url, data=data, files=files, headers=headers)
        else:
            data = {
                'title': title,
                'client': client,
                'signed': signed,
                'text': text
            }
            response = requests.post(url, json=data, headers=self.headers)
        
        return response.json()

    def get_contracts(self):
        url = f"{self.base_url}/contracts/"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def extract_clauses(self, contract_id):
        url = f"{self.base_url}/contracts/{contract_id}/clauses/"
        response = requests.post(url, headers=self.headers)
        return response.json()

# Usage
api = ContractPlatformAPI('http://localhost:8000/api', 'your-jwt-token')

# Upload contract with file
result = api.upload_contract(
    title='Service Agreement',
    client='Acme Corp',
    file_path='contract.pdf'
)

print(f"Contract ID: {result['contract_id']}")
print(f"Approved: {result['approved']}")

# Extract clauses
clauses = api.extract_clauses(result['contract_id'])
print(f"Found {clauses['clause_count']} clauses")
```

---

## Support and Contact

For API support, integration help, or bug reports:

- **Documentation**: This guide
- **Testing**: Use the provided test suite for reference implementations
- **Environment**: Ensure all required environment variables are set
- **Logs**: Check the `/logs/` endpoint for debugging information

---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Contract upload and management
- AI-powered analysis and clause extraction
- Client management
- JWT authentication
- System monitoring endpoints
- Comprehensive error handling

### Planned Features
- Bulk contract processing
- Advanced search and filtering
- Contract templates
- Webhook notifications
- API versioning
- Enhanced analytics
