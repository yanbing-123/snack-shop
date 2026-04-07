"""
认证 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from src.core.database import get_db
from src.services.auth_service import AuthService
from src.models.auth import User

router = APIRouter()
security = HTTPBearer()


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user_id: int
    username: str


class AddRailwayAccountRequest(BaseModel):
    """添加 12306 账号请求"""
    railway_username: str
    railway_password: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    payload = User.verify_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
        )
    
    user_id = int(payload.get("sub"))
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    
    return user


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    try:
        auth_service = AuthService(db)
        user, access_token, refresh_token = await auth_service.register(
            username=request.username,
            email=request.email,
            password=request.password,
            phone=request.phone,
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            username=user.username,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    try:
        auth_service = AuthService(db)
        user, access_token, refresh_token = await auth_service.login(
            username=request.username,
            password=request.password,
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            username=user.username,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: dict, db: AsyncSession = Depends(get_db)):
    """刷新令牌"""
    try:
        refresh_token = request.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少刷新令牌",
            )
        
        auth_service = AuthService(db)
        new_access_token, new_refresh_token = await auth_service.refresh_token(refresh_token)
        
        # 获取用户信息
        payload = User.verify_token(new_refresh_token)
        user_id = int(payload.get("sub"))
        user = await auth_service.get_user_by_id(user_id)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user_id=user.id,
            username=user.username,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/railway-account")
async def add_railway_account(
    request: AddRailwayAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加 12306 账号"""
    try:
        auth_service = AuthService(db)
        account = await auth_service.add_railway_account(
            user_id=current_user.id,
            railway_username=request.railway_username,
            railway_password=request.railway_password,
        )
        
        return {
            "account_id": account.id,
            "username": account.username,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/railway-accounts")
async def get_railway_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的 12306 账号列表"""
    auth_service = AuthService(db)
    accounts = await auth_service.get_railway_accounts(current_user.id)
    
    return [
        {
            "account_id": acc.id,
            "username": acc.username,
            "is_active": acc.is_active,
            "last_login": acc.last_login.isoformat() if acc.last_login else None,
            "created_at": acc.created_at.isoformat(),
        }
        for acc in accounts
    ]
