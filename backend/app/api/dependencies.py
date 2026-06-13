from fastapi import Depends, HTTPException, status

from app.models.task import User
from app.users import current_active_user


get_current_user = current_active_user


def require_client(user: User = Depends(get_current_user)) -> User:
    if user.role != "client":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有普通用户可以上传视频")
    return user


def require_counselor(user: User = Depends(get_current_user)) -> User:
    if user.role != "counselor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有心理咨询师可以访问该资源")
    return user
