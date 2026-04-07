from dataclasses import dataclass

from config.settings import get_settings
from db.models import Pack
from db.uow import SQLAlchemyUnitOfWork
from db.models import Purchase
from enums import PaymentStatus
from services.providers.payment import get_payment_provider


@dataclass(slots=True)
class PurchaseFlowResult:
    success: bool
    purchase_id: int | None = None
    payment_url: str | None = None
    provider: str | None = None
    status: PaymentStatus | None = None
    error: str | None = None


class PackService:
    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.settings = get_settings()

    async def _get_active_provider_name(self) -> str:
        from_db = await self.uow.global_setting_repo.get("payment_provider")
        return (from_db or self.settings.PAYMENT_PROVIDER or "mock").strip().lower()

    async def get_active_provider_name(self) -> str:
        return await self._get_active_provider_name()

    async def get_active_packs(self) -> list[Pack]:
        return await self.uow.pack_repo.list_active()

    async def get_pack(self, pack_id: int) -> Pack | None:
        return await self.uow.pack_repo.get(pack_id)

    async def mock_purchase_pack(self, user_id: int, pack_id: int) -> bool:
        """
        Simulates purchasing a pack. Deducts money (mocked), adds generations, records purchase.
        """
        result = await self.create_purchase(user_id=user_id, pack_id=pack_id, buyer_email=f"user_{user_id}@autogeneracia21.ru", force_provider="mock")
        return result.success

    async def create_purchase(
        self,
        *,
        user_id: int,
        pack_id: int,
        buyer_email: str,
        force_provider: str | None = None,
        payment_method: str | None = None,
    ) -> PurchaseFlowResult:
        pack = await self.uow.pack_repo.get(pack_id)
        if not pack or not pack.is_active:
            return PurchaseFlowResult(success=False, error="Pack not found or inactive")

        provider_name = (force_provider or await self._get_active_provider_name()).strip().lower()
        provider = get_payment_provider(provider_name)
        provider_result = await provider.create_payment(user_id=user_id, pack=pack, buyer_email=buyer_email, payment_method=payment_method)

        is_mock = provider_result.provider == "mock"
        initial_status = PaymentStatus.CONFIRMED if is_mock else PaymentStatus.PENDING
        purchase = Purchase(
            user_id=user_id,
            pack_id=pack.id,
            payment_status=initial_status,
            provider=provider_result.provider,
            external_invoice_id=provider_result.invoice_id,
            amount=provider_result.amount,
            currency=provider_result.currency or "RUB",
            buyer_email=buyer_email,
        )
        await self.uow.purchase_repo.add(purchase)

        if is_mock:
            await self.uow.user_balance_repo.add_generations(user_id, pack.generations_count)

        return PurchaseFlowResult(
            success=True,
            purchase_id=purchase.id,
            payment_url=provider_result.payment_url,
            provider=provider_result.provider,
            status=initial_status,
        )

    async def confirm_purchase(
        self,
        *,
        external_invoice_id: str,
        amount: float | None = None,
        currency: str | None = None,
        buyer_email: str | None = None,
    ) -> bool:
        purchase = await self.uow.purchase_repo.get_by_external_invoice_id(external_invoice_id)
        if not purchase:
            return False

        if purchase.payment_status == PaymentStatus.CONFIRMED:
            return True

        if purchase.payment_status != PaymentStatus.PENDING:
            return False

        purchase.payment_status = PaymentStatus.CONFIRMED
        if amount is not None:
            purchase.amount = amount
        if currency:
            purchase.currency = currency
        if buyer_email:
            purchase.buyer_email = buyer_email
            user = await self.uow.user_repo.get(purchase.user_id)
            if user and not user.email:
                user.email = buyer_email

        pack = await self.uow.pack_repo.get(purchase.pack_id)
        if not pack:
            return False
        await self.uow.user_balance_repo.add_generations(purchase.user_id, pack.generations_count)
        return True

    async def fail_purchase(
        self,
        *,
        external_invoice_id: str,
        amount: float | None = None,
        currency: str | None = None,
        buyer_email: str | None = None,
    ) -> bool:
        purchase = await self.uow.purchase_repo.get_by_external_invoice_id(external_invoice_id)
        if not purchase:
            return False

        if purchase.payment_status == PaymentStatus.CONFIRMED:
            return True

        purchase.payment_status = PaymentStatus.FAILED
        if amount is not None:
            purchase.amount = amount
        if currency:
            purchase.currency = currency
        if buyer_email:
            purchase.buyer_email = buyer_email
            user = await self.uow.user_repo.get(purchase.user_id)
            if user and not user.email:
                user.email = buyer_email
        return True
