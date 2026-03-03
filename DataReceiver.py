from fastapi import FastAPI, Header, HTTPException, Depends, Request
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import json
import uvicorn
import boto3
import csv
from io import StringIO

# ======================================================

# APP INIT

# ======================================================

app = FastAPI(title="Snowflake Secure Receiver API", version="3.0")

# ======================================================

# CONFIGURATION (SET THESE IN ENV VARIABLES IN PROD)

# ======================================================

JWT_SECRET = os.getenv("JWT_SECRET")
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

# ======================================================

# S3 CLIENT INITIALIZATION

# ======================================================

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# ======================================================

# RESPONSE MODELS

# ======================================================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class DataResponse(BaseModel):
    status: str
    message: str
    record_count: int

# ======================================================

# S3 DATA FETCH FUNCTION

# ======================================================

def get_customer_data_from_s3(limit=None):
    """
    Fetch customer data from S3 and return as JSON.
    
    Args:
        limit (int): Maximum number of records to return. None returns all records.
    
    Returns:
        dict: JSON response with status and data
    """
    try:
        response = s3.get_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key="customerdata/RBAC_2026-03-01-1622.csv"
        )
        
        # Read and decode the CSV data
        csv_content = response["Body"].read().decode("utf-8")
        
        # Parse CSV
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        # Convert to list of dictionaries
        records = []
        for idx, row in enumerate(reader, 1):
            if limit and idx > limit:
                break
            records.append(row)
        
        # Return as JSON response
        return {
            "status": "success",
            "count": len(records),
            "data": records
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

# ======================================================

# TOKEN CREATION

# ======================================================

def create_access_token():
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    payload = {
        "sub": "snowflake-client",
        "iat": datetime.utcnow(),
        "exp": expire
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token


# ======================================================

# TOKEN VALIDATION DEPENDENCY

# ======================================================

async def verify_jwt(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        scheme, token = authorization.split()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ======================================================

# AUTH ENDPOINT — CLIENT GETS TOKEN

# ======================================================

@app.post("/auth/token", response_model=TokenResponse)
async def generate_token(x_api_key: str = Header(None)):
    if x_api_key != CLIENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = create_access_token()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRY_HOURS * 3600
    )

# ======================================================

# PROTECTED INGEST ENDPOINT — CLIENT SENDS DATA

# ======================================================

@app.post("/ingest/data", response_model=DataResponse)
async def receive_data(request: Request, token: dict = Depends(verify_jwt)):
    payload = await request.json()

    if not payload:
        raise HTTPException(status_code=400, detail="Empty payload")

    print("\n===== DATA RECEIVED FROM SNOWFLAKE =====")
    print(json.dumps(payload, indent=2))
    print("=========================================\n")

    record_count = len(payload) if isinstance(payload, list) else 1

    return DataResponse(
        status="success",
        message="Data received successfully",
        record_count=record_count
    )

# ======================================================

# PROTECTED FETCH ENDPOINT — FETCH DATA FROM S3

# ======================================================

@app.get("/fetch/customers")
async def fetch_customers(limit: int = None, token: dict = Depends(verify_jwt)):
    """
    Fetch customer data from S3 as JSON.
    
    Query Parameters:
        limit (int, optional): Maximum number of records to return. Default: None (all records)
    
    Returns:
        JSON: Customer records from S3
    """
    result = get_customer_data_from_s3(limit=limit)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Failed to fetch data"))
    
    return result

# ======================================================

# HEALTH CHECK

# ======================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ======================================================

# LOCAL RUN

# ======================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)