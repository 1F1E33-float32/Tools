import sys


class Logger:
    @staticmethod
    def InitConsole(colorful: bool = True) -> None:
        pass

    @staticmethod
    def Log(message) -> None:
        if message is None:
            return
        sys.stdout.write(str(message) + "\n")

    @staticmethod
    def LogWarn(message) -> None:
        if message is None:
            return
        sys.stdout.write(str(message) + "\n")

    @staticmethod
    def LogError(message) -> None:
        if message is None:
            return
        sys.stderr.write(str(message) + "\n")

    @staticmethod
    def LogHint(message) -> None:
        if message is None:
            return
        sys.stdout.write(str(message) + "\n")
