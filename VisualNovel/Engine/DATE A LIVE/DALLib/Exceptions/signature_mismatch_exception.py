class SignatureMismatchException(Exception):
    def __init__(self, expected_sig: str, read_sig: str):
        message = f"The read signature does not match the expected signature! Expected {expected_sig} got {read_sig}.)"
        super().__init__(message)
        self.expected_sig = expected_sig
        self.read_sig = read_sig
