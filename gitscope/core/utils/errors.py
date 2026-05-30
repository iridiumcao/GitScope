class GitScopeError(RuntimeError):
    """Base class for application-facing errors."""


class InvalidRepositoryError(GitScopeError):
    """Raised when a path is not a valid Git repository."""


class InvalidBranchError(GitScopeError):
    """Raised when a branch filter does not exist."""


class InvalidDateRangeError(GitScopeError):
    """Raised when the requested date range is invalid."""


class OutputDirectoryError(GitScopeError):
    """Raised when the output directory cannot be created or written."""


class GitCommandError(GitScopeError):
    """Raised when a Git CLI command fails."""
