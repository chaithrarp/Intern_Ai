"""
JWT Authentication Utilities
Handles token creation, validation, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# ============================================
# CONFIGURATION
# ============================================

# SECRET KEY - In production, use environment variable!
# Generate a secure key with: openssl rand -hex 32
SECRET_KEY = "your-secret-key-change-this-in-production-use-env-variable"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ============================================
# PYDANTIC MODELS
# ============================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str

# ============================================
# JWT TOKEN FUNCTIONS
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token
    
    Args:
        data: Dictionary to encode in token
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            return None
        
        return TokenData(username=username, user_id=user_id)
    
    except JWTError:
        return None

# ============================================
# DEPENDENCY FUNCTIONS
# ============================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current authenticated user from token
    
    This is a FastAPI dependency that can be used to protect endpoints
    
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Hello {current_user.username}"}
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        User object if authenticated
    
    Raises:
        HTTPException if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    # Get user from database
    from auth_database import get_user_by_id
    
    user_dict = get_user_by_id(token_data.user_id)
    if user_dict is None:
        raise credentials_exception
    
    # Convert to User model
    user = User(
        id=user_dict["id"],
        username=user_dict["username"],
        email=user_dict["email"],
        full_name=user_dict.get("full_name"),
        is_active=user_dict.get("is_active", True)
    )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user and ensure they are active
    
    Args:
        current_user: User from get_current_user dependency
    
    Returns:
        User object if active
    
    Raises:
        HTTPException if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user_id from token without full validation
    Useful for optional authentication
    
    Args:
        token: JWT token string
    
    Returns:
        user_id if token is valid, None otherwise
    """
    token_data = verify_token(token)
    if token_data:
        return token_data.user_id
    return None

# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING JWT AUTHENTICATION")
    print("=" * 50)
    
    # Create a test token
    print("\n1. Creating test token...")
    test_data = {
        "sub": "testuser",
        "user_id": 1
    }
    
    token = create_access_token(test_data)
    print(f"   Token (first 50 chars): {token[:50]}...")
    
    # Verify token
    print("\n2. Verifying token...")
    token_data = verify_token(token)
    if token_data:
        print(f"   ✅ Token valid")
        print(f"   - Username: {token_data.username}")
        print(f"   - User ID: {token_data.user_id}")
    else:
        print("   ❌ Token invalid")
    
    # Test invalid token
    print("\n3. Testing invalid token...")
    invalid_token = "invalid.token.here"
    token_data = verify_token(invalid_token)
    if token_data:
        print("   ❌ Should have been invalid!")
    else:
        print("   ✅ Correctly rejected invalid token")
    
    print("\n✅ JWT authentication test complete!")