# Snowflake Secure Receiver API

A FastAPI-based REST API for securely receiving data from Snowflake and fetching customer data from AWS S3, with JWT authentication and CSV-to-JSON conversion.

## Features

- **JWT Authentication**: Secure token-based access to protected endpoints
- **Data Ingestion**: Receive data from Snowflake via POST endpoint
- **S3 Integration**: Fetch customer CSV data from AWS S3 bucket
- **JSON Response**: All data returned as structured JSON
- **CSV Parsing**: Automatic CSV-to-JSON conversion with proper field mapping
- **Health Check**: Built-in health check endpoint
- **Error Handling**: Comprehensive error responses with descriptive messages

## Tech Stack

- **Framework**: FastAPI 0.131.0
- **Server**: Uvicorn 0.41.0
- **Authentication**: Python-jose (JWT)
- **AWS**: boto3
- **Python**: 3.11+

## Installation

### Prerequisites

- Python 3.11 or higher
- Virtual environment (venv)
- AWS credentials configured
- JWT secret for token generation

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd SnowflakeToAPIDataPush
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows PowerShell
   source venv/bin/activate      # Linux/Mac
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (create `.env` file)

   ```env
   # JWT Configuration
   JWT_SECRET=your-jwt-secret-key-here

   # API Key for token generation
   CLIENT_API_KEY=your-api-key-here

   # AWS Configuration
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_REGION=us-east-1

   # S3 Configuration
   S3_BUCKET_NAME=your-s3-bucket-name
   ```

## API Endpoints

### 1. Health Check (Public)

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-03-03T12:34:56.789123"
}
```

---

### 2. Generate Token (Public)

```http
POST /auth/token
Header: X-API-Key: <CLIENT_API_KEY>
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

### 3. Ingest Data (Protected)

```http
POST /ingest/data
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
[
  {
    "customer_id": 1,
    "name": "ACME Corp",
    "email": "contact@acme.com"
  },
  {
    "customer_id": 2,
    "name": "Tech Solutions",
    "email": "info@techsolutions.com"
  }
]
```

**Response:**

```json
{
  "status": "success",
  "message": "Data received successfully",
  "record_count": 2
}
```

---

### 4. Fetch Customers from S3 (Protected)

```http
GET /fetch/customers?limit=5
Authorization: Bearer <access_token>
```

**Query Parameters:**

- `limit` (optional): Maximum number of records to return. Default: all records

**Response:**

```json
{
  "status": "success",
  "count": 5,
  "data": [
    {
      "C_CUSTKEY": "1",
      "C_NAME": "Customer#000000001",
      "C_ADDRESS": "IVhzIApeRb ot,c,E",
      "C_NATIONKEY": "15",
      "C_PHONE": "25-989-741-2988",
      "C_ACCTBAL": "711.56",
      "C_MKTSEGMENT": "BUILDING",
      "C_COMMENT": "to the even, regular platelets..."
    },
    ...
  ]
}
```

## Usage Examples

### Example 1: Get Token and Fetch Data

```bash
# 1. Get JWT token
curl -X POST "http://localhost:5000/auth/token" \
  -H "X-API-Key: my-api-key"

# 2. Use token to fetch customers (limit 5)
curl -X GET "http://localhost:5000/fetch/customers?limit=5" \
  -H "Authorization: Bearer <your-token-here>"
```

### Example 2: Ingest Snowflake Data

```bash
# 1. Get token
TOKEN=$(curl -s -X POST "http://localhost:5000/auth/token" \
  -H "X-API-Key: my-api-key" | jq -r '.access_token')

# 2. Send data to API
curl -X POST "http://localhost:5000/ingest/data" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"customer_id": 1, "name": "Test Customer", "email": "test@example.com"}
  ]'
```

## Running the Application

### Development Server

```bash
python DataReceiver.py
```

The API will start on `http://0.0.0.0:5000`

### Access API Documentation

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## Project Structure

```
SnowflakeToAPIDataPush/
├── DataReceiver.py          # Main FastAPI application
├── DataReceiver.py          # S3 data fetching utility
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in repo)
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## Environment Variables

| Variable                | Description                  | Example               |
| ----------------------- | ---------------------------- | --------------------- |
| `JWT_SECRET`            | Secret key for JWT encoding  | `your-secret-key-123` |
| `CLIENT_API_KEY`        | API key for token generation | `my-api-key-456`      |
| `AWS_ACCESS_KEY_ID`     | AWS access key               | `AKIARGKHWWCELA...`   |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key               | `0gvZ15XBcUbLsDr1...` |
| `AWS_REGION`            | AWS region for S3            | `us-east-1`           |
| `S3_BUCKET_NAME`        | S3 bucket name               | `awstoapidatashare`   |

## Development Workflow

### Feature Development

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Commit with descriptive messages: `git commit -m "feat: Add new feature"`
4. Push to origin: `git push origin feature/your-feature-name`
5. Create a Pull Request on GitHub
6. Wait for review and merge to main

### Current Feature Branch

- `feature/s3-customer-fetch-endpoint`: S3 integration with customer data fetching endpoint

## Dependencies

See `requirements.txt` for the complete list. Key packages:

- fastapi==0.131.0
- uvicorn==0.41.0
- boto3
- python-jose
- python-dotenv

## Authentication Flow

1. Client sends request with `X-API-Key` header to `/auth/token`
2. Server validates API key and returns JWT token
3. Client includes token in `Authorization: Bearer <token>` header for protected endpoints
4. Server validates JWT and processes request
5. Response returned as JSON

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error description here"
}
```

Common HTTP Status Codes:

- `200`: Success
- `400`: Bad request
- `401`: Unauthorized (invalid token or API key)
- `500`: Internal server error

## License

[Add your license here]

## Contributing

1. Follow the development workflow above
2. Write clear commit messages
3. Include tests for new features
4. Update README if adding new endpoints

## Contact

[Add contact information]
