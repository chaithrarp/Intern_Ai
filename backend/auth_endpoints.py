"""
Authentication API Endpoints
Add these to your main.py file

This file contains all authentication-related endpoints:
- POST /register - Create new user account
- POST /login - Login and get JWT token
- GET /users/me - Get current user info
- POST /logout - Logout (client-side token removal)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from auth import (
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    User,
    UserCreate,
    UserLogin
)

from auth_database import (
    create_user,
    authenticate_user,
    get_user_by_username,
    get_user_by_email
)

# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# ============================================
# REGISTRATION ENDPOINT
# ============================================

@auth_router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """
    Register a new user
    
    Request body:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "securepassword123",
        "full_name": "John Doe"  // optional
    }
    
    Returns:
    {
        "message": "User created successfully",
        "user_id": 1,
        "username": "john_doe"
    }
    """
    # Check if username already exists
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength (basic)
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Create user
    user_id = create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return {
        "message": "User created successfully",
        "user_id": user_id,
        "username": user_data.username
    }

# ============================================
# LOGIN ENDPOINT
# ============================================

@auth_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """
    Login with username/email and password
    
    Request body:
    {
        "username": "john_doe",  // or email
        "password": "securepassword123"
    }
    
    Returns:
    {
        "access_token": "eyJhbGc...",
        "token_type": "bearer"
    }
    """
    # Authenticate user
    user = authenticate_user(user_credentials.username, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    print(f"✅ User logged in: {user['username']}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ============================================
# OAUTH2 COMPATIBLE LOGIN (OPTIONAL)
# ============================================

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible login endpoint
    This is used by Swagger UI's "Authorize" button
    
    Form data:
    - username: john_doe (or email)
    - password: securepassword123
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ============================================
# GET CURRENT USER
# ============================================

@auth_router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current logged-in user information
    
    Requires: Authorization header with Bearer token
    
    Returns:
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "is_active": true
    }
    """
    return current_user

# ============================================
# LOGOUT (CLIENT-SIDE)
# ============================================

@auth_router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout endpoint
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token from storage. This endpoint just confirms
    the user was authenticated.
    
    Returns:
    {
        "message": "Successfully logged out"
    }
    """
    print(f"✅ User logged out: {current_user.username}")
    
    return {
        "message": "Successfully logged out",
        "username": current_user.username
    }

# ============================================
# USAGE IN main.py
# ============================================

"""
To use these endpoints, add this to your main.py:

1. Import at top:
   from auth_endpoints import auth_router

2. Include router:
   app.include_router(auth_router)

3. Initialize auth database on startup:
   from auth_database import init_auth_database
   
   @app.on_event("startup")
   async def startup_event():
       init_database()  # existing
       init_auth_database()  # new

4. Protect endpoints with authentication:
   from auth import get_current_active_user, User
   
   @app.post("/interview/start")
   async def start_interview(current_user: User = Depends(get_current_active_user)):
       # Only authenticated users can access
       # Use current_user.id for user-specific data
       ...
"""