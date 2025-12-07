"""
Database initialisation script.

This script initialises the database tables and creates default settings.
Use this for development. In production, use Alembic migrations.
"""

import asyncio
from app.core.database import init_db, AsyncSessionLocal
from app.core.db_models import HealthThreshold, ApplicationSettings, User
from app.core.security import get_password_hash
from app.core.config import get_settings

settings = get_settings()


async def create_default_settings():
    """
    Create default settings in the database.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Create default health thresholds
            threshold = HealthThreshold(
                check_in_hours=settings.check_in_threshold_hours,
                recon_hours=settings.recon_threshold_hours,
                pending_command_hours=settings.pending_command_threshold_hours,
                is_active=True
            )
            session.add(threshold)
            
            # Create default compliance group setting
            compliance_setting = ApplicationSettings(
                setting_key="compliance_group",
                setting_value="Compliance"
            )
            session.add(compliance_setting)
            
            # Create default monitored groups setting
            monitored_setting = ApplicationSettings(
                setting_key="monitored_groups",
                setting_value="[]"
            )
            session.add(monitored_setting)
            
            # Create admin user if it doesn't exist
            admin_user = User(
                username=settings.admin_username,
                hashed_password=settings.admin_password,
                full_name="Administrator",
                is_superuser=True,
                is_active=True
            )
            session.add(admin_user)
            
            await session.commit()
            print("✓ Default settings created successfully")
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Error creating default settings: {e}")
            raise


async def main():
    """
    Main initialisation function.
    """
    print("Initialising database...")
    print(f"Environment: {settings.environment}")
    
    try:
        await init_db()
        print("✓ Database tables created")
        
        await create_default_settings()
        print("✓ Database initialisation complete")
        
    except Exception as e:
        print(f"✗ Database initialisation failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
