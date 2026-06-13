from fastapi_users.password import PasswordHelper
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import ConsultationBinding, User


SEED_USERS = (
    ("client@example.com", "client123", "client", "演示普通用户"),
    ("counselor@example.com", "counselor123", "counselor", "演示心理咨询师"),
)


class AuthService:
    def __init__(self) -> None:
        self.password_helper = PasswordHelper()

    async def seed_demo_users(self, db: AsyncSession) -> None:
        users: dict[str, User] = {}
        for email, password, role, display_name in SEED_USERS:
            user = await db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    hashed_password=self.password_helper.hash(password),
                    role=role,
                    display_name=display_name,
                    is_active=True,
                    is_verified=True,
                    is_superuser=False,
                )
                db.add(user)
                await db.flush()
            users[email] = user

        binding = await db.scalar(
            select(ConsultationBinding).where(
                ConsultationBinding.counselor_id == users["counselor@example.com"].id,
                ConsultationBinding.client_id == users["client@example.com"].id,
            )
        )
        if binding is None:
            db.add(
                ConsultationBinding(
                    counselor_id=users["counselor@example.com"].id,
                    client_id=users["client@example.com"].id,
                )
            )
        await db.commit()


auth_service = AuthService()
