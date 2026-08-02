class RateLimitError(Exception):
    def __init__(self, retry_at):
        self.retry_at = retry_at

        if retry_at:
            super().__init__(
                f"Twitter rate limit exceeded. Please retry at {retry_at}."
            )
        else:
            super().__init__(
                "Twitter rate limit exceeded."
            )