"""Custom exceptions raised by GitScope."""


class GitScopeError(RuntimeError):
    """Base application error."""


class ValidationError(GitScopeError):
    """Raised when CLI inputs are invalid."""


class GitCommandError(GitScopeError):
    """Raised when a Git command fails."""
