class CreateProductUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, data: dict):
        async with self.uow as uow:
            result = await uow.product_repository.create(data)
            await uow.commit()
            return result
