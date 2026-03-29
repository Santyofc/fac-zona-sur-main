class UploadCertificateUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, data: dict):
        async with self.uow as uow:
            cert = await uow.certificate_repository.create(data)
            await uow.commit()
            return cert
