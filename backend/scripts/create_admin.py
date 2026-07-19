import argparse
import asyncio
from getpass import getpass

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import Role, hash_password
from app.users.models import User


async def create_or_promote(email: str, password: str | None) -> None:
    normalized_email = email.strip().casefold()
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == normalized_email))
        if user is None:
            if not password:
                raise ValueError("A password is required when creating a new administrator")
            user = User(
                email=normalized_email,
                password_hash=hash_password(password),
                role=Role.admin.value,
                display_name="Administrator",
            )
            db.add(user)
            operation = "Created"
        else:
            user.role = Role.admin.value
            user.is_active = True
            if password:
                user.password_hash = hash_password(password)
            operation = "Promoted"
        await db.commit()
        print(f"{operation} admin account: {normalized_email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin or promote an existing account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", help="Omit to be prompted without showing the password")
    parser.add_argument("--keep-password", action="store_true", help="Keep an existing user's password")
    args = parser.parse_args()
    password = None if args.keep_password else (args.password or getpass("Password: "))
    asyncio.run(create_or_promote(args.email, password))


if __name__ == "__main__":
    main()
