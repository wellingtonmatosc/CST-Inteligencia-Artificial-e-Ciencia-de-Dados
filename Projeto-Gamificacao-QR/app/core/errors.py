class AppError(Exception):
    """Erro de domínio com status HTTP e mensagem segura."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
