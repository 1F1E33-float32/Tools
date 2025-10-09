class InvalidFileFormatException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidTextureFormatException(Exception):
    def __init__(self, format_code: int):
        message = f"The texture that is currently loading contains an invalid or unknown format! (0x{format_code:08X})"
        super().__init__(message)
        self.format_code = format_code


class STSCDisassembleException(Exception):
    def __init__(self, script, reason: str):
        script_name = getattr(script, "script_name", "Unknown")
        message = f"Failed to disassemble the script file {script_name}. {reason}"
        super().__init__(message)
        self.script = script
        self.reason = reason


class SignatureMismatchException(Exception):
    def __init__(self, expected_sig: str, read_sig: str):
        message = f"The read signature does not match the expected signature! (Expected {expected_sig} got {read_sig}.)"
        super().__init__(message)
        self.expected_sig = expected_sig
        self.read_sig = read_sig


__all__ = ["InvalidFileFormatException", "InvalidTextureFormatException", "STSCDisassembleException", "SignatureMismatchException"]
