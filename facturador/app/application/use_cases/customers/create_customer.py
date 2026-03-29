class CreateCustomerUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, data: dict):
        async with self.uow as uow:
            result = await uow.customer_repository.create(data)
            await uow.commit()
            return result
