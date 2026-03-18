from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.repo import (
    SQLAlchemyUserRepository,
    AiModelRepository,
    TemplateRepository,
    PackRepository,
    UserBalanceRepository,
    PurchaseRepository,
    GenerationRepository,
    ReferralRepository,
    UserActionRepository,
    GlobalSettingRepository,
    MailingRepository,
    UtmCampaignRepository,
    UtmClickRepository,
    UtmRegistrationRepository,
)

from .session import SessionFactory


class SQLAlchemyUnitOfWork:
    _session_factory: async_sessionmaker[AsyncSession]
    _session: Optional[AsyncSession]

    _user_repo: Optional[SQLAlchemyUserRepository]
    _ai_model_repo: Optional[AiModelRepository]
    _template_repo: Optional[TemplateRepository]
    _pack_repo: Optional[PackRepository]
    _user_balance_repo: Optional[UserBalanceRepository]
    _purchase_repo: Optional[PurchaseRepository]
    _generation_repo: Optional[GenerationRepository]
    _referral_repo: Optional[ReferralRepository]
    _user_action_repo: Optional[UserActionRepository]
    _global_setting_repo: Optional[GlobalSettingRepository]
    _mailing_repo: Optional[MailingRepository]
    _utm_campaign_repo: Optional[UtmCampaignRepository]
    _utm_click_repo: Optional[UtmClickRepository]
    _utm_registration_repo: Optional[UtmRegistrationRepository]

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = SessionFactory) -> None:
        self._session_factory = session_factory
        self._session = None
        
        self._user_repo = None
        self._ai_model_repo = None
        self._template_repo = None
        self._pack_repo = None
        self._user_balance_repo = None
        self._purchase_repo = None
        self._generation_repo = None
        self._referral_repo = None
        self._user_action_repo = None
        self._global_setting_repo = None
        self._mailing_repo = None
        self._utm_campaign_repo = None
        self._utm_click_repo = None
        self._utm_registration_repo = None

    # ---------- public accessors ----------

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("SQLAlchemyUnitOfWork is not entered. Use 'async with SQLAlchemyUnitOfWork(...) as uow:'")
        return self._session

    @property
    def user_repo(self) -> SQLAlchemyUserRepository:
        assert self._user_repo is not None, "user_repo is not initialized"
        return self._user_repo

    @property
    def ai_model_repo(self) -> AiModelRepository:
        assert self._ai_model_repo is not None, "ai_model_repo is not initialized"
        return self._ai_model_repo

    @property
    def template_repo(self) -> TemplateRepository:
        assert self._template_repo is not None, "template_repo is not initialized"
        return self._template_repo

    @property
    def pack_repo(self) -> PackRepository:
        assert self._pack_repo is not None, "pack_repo is not initialized"
        return self._pack_repo

    @property
    def user_balance_repo(self) -> UserBalanceRepository:
        assert self._user_balance_repo is not None, "user_balance_repo is not initialized"
        return self._user_balance_repo

    @property
    def purchase_repo(self) -> PurchaseRepository:
        assert self._purchase_repo is not None, "purchase_repo is not initialized"
        return self._purchase_repo

    @property
    def generation_repo(self) -> GenerationRepository:
        assert self._generation_repo is not None, "generation_repo is not initialized"
        return self._generation_repo

    @property
    def referral_repo(self) -> ReferralRepository:
        assert self._referral_repo is not None, "referral_repo is not initialized"
        return self._referral_repo

    @property
    def user_action_repo(self) -> UserActionRepository:
        assert self._user_action_repo is not None, "user_action_repo is not initialized"
        return self._user_action_repo

    @property
    def global_setting_repo(self) -> GlobalSettingRepository:
        assert self._global_setting_repo is not None, "global_setting_repo is not initialized"
        return self._global_setting_repo

    @property
    def mailing_repo(self) -> MailingRepository:
        assert self._mailing_repo is not None, "mailing_repo is not initialized"
        return self._mailing_repo

    @property
    def utm_campaign_repo(self) -> UtmCampaignRepository:
        assert self._utm_campaign_repo is not None, "utm_campaign_repo is not initialized"
        return self._utm_campaign_repo

    @property
    def utm_click_repo(self) -> UtmClickRepository:
        assert self._utm_click_repo is not None, "utm_click_repo is not initialized"
        return self._utm_click_repo

    @property
    def utm_registration_repo(self) -> UtmRegistrationRepository:
        assert self._utm_registration_repo is not None, "utm_registration_repo is not initialized"
        return self._utm_registration_repo

    # ---------- context manager ----------

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        await self._session.begin()

        self._user_repo = SQLAlchemyUserRepository(self._session)
        self._ai_model_repo = AiModelRepository(self._session)
        self._template_repo = TemplateRepository(self._session)
        self._pack_repo = PackRepository(self._session)
        self._user_balance_repo = UserBalanceRepository(self._session)
        self._purchase_repo = PurchaseRepository(self._session)
        self._generation_repo = GenerationRepository(self._session)
        self._referral_repo = ReferralRepository(self._session)
        self._user_action_repo = UserActionRepository(self._session)
        self._global_setting_repo = GlobalSettingRepository(self._session)
        self._mailing_repo = MailingRepository(self._session)
        self._utm_campaign_repo = UtmCampaignRepository(self._session)
        self._utm_click_repo = UtmClickRepository(self._session)
        self._utm_registration_repo = UtmRegistrationRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, traceback) -> bool:
        if self._session is None:
            return False

        try:
            if exc_type:
                await self._session.rollback()
            else:
                await self._session.commit()
        finally:
            await self._session.close()
            self._session = None
            
            self._user_repo = None
            self._ai_model_repo = None
            self._template_repo = None
            self._pack_repo = None
            self._user_balance_repo = None
            self._purchase_repo = None
            self._generation_repo = None
            self._referral_repo = None
            self._user_action_repo = None
            self._global_setting_repo = None
            self._mailing_repo = None
            self._utm_campaign_repo = None
            self._utm_click_repo = None
            self._utm_registration_repo = None

        return False

    # ---------- optional helpers ----------

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


def get_uow() -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork(SessionFactory)
