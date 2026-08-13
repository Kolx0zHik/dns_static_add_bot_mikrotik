class AppError(Exception):
    """Base exception for expected application errors."""

    user_message = "Произошла ошибка. Попробуйте позже."


class ValidationError(AppError):
    """Raised when user input does not pass validation."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class RecordAlreadyExistsError(AppError):
    """Raised when a MikroTik DNS static record already exists."""

    user_message = "Запись уже существует."


class SshConnectionError(AppError):
    """Raised when SSH connection cannot be established."""

    user_message = "Не удалось подключиться к MikroTik. Попробуйте позже."


class SshAuthenticationError(AppError):
    """Raised when SSH authentication fails."""

    user_message = "Ошибка авторизации на MikroTik."


class SshCommandError(AppError):
    """Raised when a RouterOS command fails."""

    user_message = "Не удалось выполнить команду на MikroTik."
