class GetInvoiceUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, tenant_id, invoice_id):
        async with self.uow as uow:
            return await uow.invoice_repository.get_by_id(tenant_id, invoice_id)
