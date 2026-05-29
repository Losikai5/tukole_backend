# scripts/seed_admin.py
import asyncio
import getpass

from sqlalchemy import text

# --- All four imports now confirmed against your actual project files ---
from app.core.database import engine, local_session   # engine + the project's
                                                       # own session factory
from app.core.models import User, UserRole             # User model + UserRole enum
from app.modules.Auth.utils import hash_password       # the real hashing helper
#   note the capital A in Auth — must match the folder name exactly so the
#   import still works if TUKOLE is ever deployed to a case-sensitive Linux server
# ------------------------------------------------------------------------


async def wipe_all_data(session) -> None:
    """Empty every data table but preserve Alembic's migration history."""
    # Ask Postgres for every table in the public schema dynamically, so we
    # never maintain a hand-written list that drifts out of sync when a new
    # module is added. alembic_version is excluded so Alembic keeps its
    # record of which migration the schema currently sits at.
    result = await session.execute(
        text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
        )
    )
    tables = [row[0] for row in result]

    if not tables:
        print("No tables found to wipe.")
        return

    # TRUNCATE empties tables instantly; CASCADE follows foreign keys so the
    # order of tables doesn't matter. RESTART IDENTITY is harmless here since
    # your primary keys are UUIDs, but kept for correctness.
    table_list = ", ".join(tables)
    await session.execute(
        text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE")
    )
    print(f"Wiped {len(tables)} tables: {table_list}")


async def create_admin(session) -> None:
    """Insert exactly one admin user, matching the real User model."""
    # first_name, last_name, username and email are all nullable=False in
    # your model, so each one MUST be supplied or the insert is rejected.
    first_name = input("Admin first name: ").strip()
    last_name = input("Admin last name: ").strip()
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip()
    # getpass hides the password as you type and keeps it out of shell
    # history — the same secrets-hygiene principle from the .env discussion.
    password = getpass.getpass("Admin password: ")

    admin = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        # hash_password uses the project's shared bcrypt CryptContext, so the
        # admin's password is hashed identically to every normal user's —
        # which means verify_password at login will validate it correctly.
        # The column is named `hashed_password` in your model; the attribute
        # name must match exactly or SQLAlchemy won't map the value in.
        hashed_password=hash_password(password),
        role=UserRole.ADMIN,   # enum member; stores as a string in the VARCHAR
        is_active=True,        # default is False — must be True or the admin
                               # may be blocked at login
        is_verified=True,      # default is False — set True so no separate
                               # verification step is needed
        # uid, created_at, updated_at fill themselves via model defaults
        # and server_default, so we leave them alone.
    )
    session.add(admin)
    print(f"Created admin user: {email}")


async def main() -> None:
    # local_session is your project's own configured session factory,
    # carrying expire_on_commit=False so the admin object stays readable
    # after the commit. We reuse it rather than building a session by hand.
    async with local_session() as session:
        await wipe_all_data(session)
        await create_admin(session)
        # A single commit at the very end makes the whole operation atomic:
        # if create_admin fails, the wipe rolls back too, so you're never
        # left with an emptied database and no admin in it.
        await session.commit()
        print("Done. Database now contains exactly one user (the admin).")


if __name__ == "__main__":
    asyncio.run(main())