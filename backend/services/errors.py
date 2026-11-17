"""Domain error carrying an HTTP status and a stable error_code."""


class AppError(Exception):
    def __init__(self, message, error_code, status_code):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
