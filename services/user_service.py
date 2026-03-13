from typing import Optional

from db.models import User, Referral, UserBalance
from db.uow import SQLAlchemyUnitOfWork


class UserService:
    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self.uow = uow

    async def get_or_create_user(self, user_id: int, username: str | None = None, full_name: str | None = None) -> User:
        user = await self.uow.user_repo.get_by_id(user_id)
        if not user:
            user = User(user_id=user_id, username=username, full_name=full_name)
            await self.uow.user_repo.create(user)
        else:
            # Update user info if changed
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True
            if updated:
                await self.uow.user_repo.update(user)
                
        # Ensure user has a balance record
        await self.uow.user_balance_repo.get_or_create(user_id)
        return user

    async def accept_agreement(self, user_id: int) -> bool:
        user = await self.uow.user_repo.get_by_id(user_id)
        if user and not user.has_accepted_agreement:
            user.has_accepted_agreement = True
            await self.uow.user_repo.update(user)
            return True
        return False

    async def process_referral(self, user: User, referrer_code: str) -> bool:
        """
        Processes a referral code. Returns True if successfully applied.
        """
        import logging
        import datetime
        logger = logging.getLogger(__name__)

        now = datetime.datetime.now(datetime.timezone.utc)
        created_at = user.created_at
        # Make sure created_at is timezone-aware for comparison
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=datetime.timezone.utc)
        age_seconds = (now - created_at).total_seconds()

        if age_seconds > 3600:
            logger.info("Referral skipped: user %s account is too old (%.0fs)", user.user_id, age_seconds)
            return False

        referrer = await self.uow.user_repo.get_by_referral_code(referrer_code)
        if not referrer:
            logger.info("Referral skipped: code '%s' not found", referrer_code)
            return False
        if referrer.user_id == user.user_id:
            logger.info("Referral skipped: user %s tried to use own code", user.user_id)
            return False

        existing_referral = await self.uow.referral_repo.get_by_referred(user.user_id)
        if existing_referral:
            logger.info("Referral skipped: user %s already has a referral", user.user_id)
            return False

        # Create referral record
        referral = Referral(referrer_id=referrer.user_id, referred_id=user.user_id, bonus_applied=True)
        await self.uow.referral_repo.add(referral)

        # Add bonus generation to referrer
        await self.uow.user_balance_repo.add_generations(referrer.user_id, 1)
        logger.info("Referral applied: user %s referred by user %s, +1 gen", user.user_id, referrer.user_id)

        return True

    async def get_profile_info(self, user_id: int) -> dict:
        user = await self.uow.user_repo.get_by_id(user_id)
        balance = await self.uow.user_balance_repo.get_or_create(user_id)
        referrals_count = await self.uow.referral_repo.count_by_referrer(user_id)
        
        return {
            "user": user,
            "balance": balance.generations_remaining,
            "referrals_count": referrals_count,
        }
