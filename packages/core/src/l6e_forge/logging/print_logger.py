from l6e_forge.logging.base import ILogger


class PrintLogger(ILogger):
    def info(self, message: str) -> None:
        print(f"INFO: {message}")

    def error(self, message: str) -> None:
        print(f"ERROR: {message}")

    def warning(self, message: str) -> None:
        print(f"WARNING: {message}")

    def debug(self, message: str) -> None:
        print(f"DEBUG: {message}")

    def critical(self, message: str) -> None:
        print(f"CRITICAL: {message}")

    def exception(self, message: str, exc: Exception | None = None) -> None:
        print(f"EXCEPTION: {message}")
        if exc:
            print(f"EXCEPTION: {repr(exc)}")
            print(f"Exception type: {type(exc)}")
            print(f"Exception message: {exc.args}")
            print(f"Exception traceback: {exc.__traceback__}")

    def fatal(self, message: str) -> None:
        print(f"FATAL: {message}")

    def log(self, level: int, message: str) -> None:
        print(f"{level}: {message}")

    def isEnabledFor(self, level: int) -> bool:
        return True
