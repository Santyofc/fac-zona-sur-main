class ListCustomersUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, tenant_id):
        async with self.uow as uow:
            return await uow.customer_repository.list_by_tenant(tenant_id)
