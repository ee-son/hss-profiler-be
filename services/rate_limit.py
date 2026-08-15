class RateLimitError(Exception):
    def __init__(self, retry_at=None, endpoint=None):
        self.retry_at = retry_at
        self.endpoint = endpoint

        if retry_at and endpoint:
            message = (
                f"Twitter rate limit exceeded for {endpoint}. "
                f"Please retry at {retry_at}."
            )
        elif retry_at:
            message = (
                f"Twitter rate limit exceeded. "
                f"Please retry at {retry_at}."
            )
        else:
            message = "Twitter rate limit exceeded."

        super().__init__(message)