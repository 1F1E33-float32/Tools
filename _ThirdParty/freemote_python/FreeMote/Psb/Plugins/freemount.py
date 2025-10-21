from io import BytesIO
from typing import Any, Dict


class FreeMountContext:
    def __init__(self, context: Dict[str, Any] | None = None) -> None:
        self.Context = context or {}
        self.ImageFormat = None

    def OpenFromShell(self, stream, type_ref) -> BytesIO | None:
        return None


class FreeMount:
    ARG_DISABLE_PLUGINS = "--disable-plugins"
    PluginsCount = 0

    @staticmethod
    def Init(path: str | None = None) -> None:
        pass

    @staticmethod
    def PrintPluginInfos(indent: int = 0) -> str:
        return ""

    @staticmethod
    def CreateContext(context: Dict[str, Any] | None = None) -> FreeMountContext:
        return FreeMountContext(context or {})
