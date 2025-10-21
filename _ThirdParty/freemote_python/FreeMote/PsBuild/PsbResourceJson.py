import json
from typing import Any, Dict, Optional


class PsbResourceJson:
    def __init__(self, psb=None, context: Dict[str, Any] | None = None) -> None:
        self.PsbVersion: Optional[int] = 3
        self.PsbType = None
        self.Platform = None
        self.CryptKey: Optional[int] = None
        self.ExternalTextures: bool = False
        self.Context: Dict[str, Any] = context or {}
        self.Resources: Dict[str, str] | None = None
        self.ExtraResources: Dict[str, str] | None = None
        self.ExtraFlattenArrays: Dict[str, list] | None = None
        self.Encoding: Optional[int] = None
        if psb is not None:
            self.PsbVersion = getattr(getattr(psb, "Header", None), "Version", 3)
            self.PsbType = getattr(psb, "Type", None)
            self.Platform = getattr(psb, "Platform", None)
            if context is not None and "CryptKey" in context:
                self.CryptKey = context.get("CryptKey")

    def SerializeToJson(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=2, ensure_ascii=False)
