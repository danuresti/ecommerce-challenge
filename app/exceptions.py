class AppError(Exception):
    """Base exception for all application-level errors."""
    pass


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""
    pass


class ValidationError(AppError):
    """Raised when input data fails business validation rules."""
    pass


class DuplicateError(AppError):
    """Raised when a uniqueness constraint would be violated."""
    pass


class InsufficientStockError(AppError):
    """Raised when a purchase is attempted with insufficient stock."""
    pass