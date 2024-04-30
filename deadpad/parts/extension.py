from typing import TYPE_CHECKING

from types import ModuleType
if TYPE_CHECKING:
    from deadpad import Editor

class Extension:
    def __init__(self, master, name:str, module:ModuleType) -> None:
        "Holds metadata and type information for the extensions."
        self.master:Editor = master
        self.name = name
        self.module = module
        self.DESCRIPTION:str = self.module.DESCRIPTION
        self.FILE_EXT:str = self.module.FILE_EXT
        self.parser:self.module.Parser | None = self.module.Parser(master) if hasattr(self.module, "Parser") else None