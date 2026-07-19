class RateLimitError(Exception):
    def __init__(self, retry_at):
        self.retry_at = retry_at
        super().__init__("Twitter rate limit exceeded.")