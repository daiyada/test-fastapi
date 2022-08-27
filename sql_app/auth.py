from datetime import datetime, timedelta
import hashlib
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .crud import get_user, get_user_by_email
from .models import User
from .schemas import TokenData


# openssl rand -hex 32
SECRET_KEY = "4debb9cc4119ba756a69f5966bec69565ae89cfe53d438cb3929d091ff8ac895"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
h = hashlib.new("sha256")

def verify_password(plain_password, hashed_password):
    """
    @brief パスワードがハッシュ化されたパスワードか同一か確認する関数
    """
    ret = False
    # crud.pyのcreate_userのfake_hashed_passwordに倣った
    if hashed_password == plain_password + "notreallyhashed":
        ret = True
    return ret

def authenticate_user(db: Session, email: str, password: str):
    """
    @brief ユーザを認証して、そのユーザを返す関数
    """
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """
    @brief アクセストークンを作成する関数
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    @brief アクセストークンを渡すことで、そのトークンに結びついたユーザを返す関数
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
            raise credentials_exception
    user = get_user(get_db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    @brief 認証済みのアクティブユーザーの取得用関数
    """
    if current_user.disabled:
        raise HTTPException(staus_code=400, detail="Inactive user")
    return current_user



