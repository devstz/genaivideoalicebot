from db.models import Pack
from db.uow import SQLAlchemyUnitOfWork
from db.models import Purchase
from enums import PaymentStatus


class PackService:
    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self.uow = uow

    async def get_active_packs(self) -> list[Pack]:
        return await self.uow.pack_repo.list_active()

    async def get_pack(self, pack_id: int) -> Pack | None:
        return await self.uow.pack_repo.get(pack_id)

    async def mock_purchase_pack(self, user_id: int, pack_id: int) -> bool:
        """
        Simulates purchasing a pack. Deducts money (mocked), adds generations, records purchase.
        """
        pack = await self.uow.pack_repo.get(pack_id)
        if not pack or not pack.is_active:
            return False

        # In a real scenario, this is where payment processing would happen.
        # We mock a successful payment here.
        
        # 1. Add generations to user balance
        await self.uow.user_balance_repo.add_generations(user_id, pack.generations_count)

        # 2. Record purchase
        purchase = Purchase(user_id=user_id, pack_id=pack.id, payment_status=PaymentStatus.CONFIRMED)
        await self.uow.purchase_repo.add(purchase)

        return True
