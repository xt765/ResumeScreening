
import asyncio
from sqlalchemy import select
from passlib.context import CryptContext
from dotenv import load_dotenv

from src.models import init_db, create_tables
import src.models as models
from src.models.user import User, RoleEnum
from src.core.config import get_settings

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def init_database():
    settings = get_settings()
    print(f"Initializing database with DSN: {settings.mysql.dsn}")
    
    # Initialize DB connection
    init_db(settings.mysql.dsn)
    
    # Create tables
    print("Creating tables...")
    await create_tables()
    
    # Create initial admin user
    async with models.async_session_factory() as session:
        # Check if admin exists
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("Creating admin user...")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                role=RoleEnum.ADMIN,
                nickname="Administrator",
                is_active=True,
                is_first_login=False
            )
            session.add(admin_user)
            await session.commit()
            print("Admin user created: admin / admin123")
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(init_database())
