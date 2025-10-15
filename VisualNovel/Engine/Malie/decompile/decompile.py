"""
┌─────────────────────────────────────┐
│  Variables Section (Vars)           │
│  - Count (uint32)                   │
│  - Variable List                    │
│    └─ Name (UTF-16LE, length flag)  │
│    └─ Parameters (uint32 pairs)     │
├─────────────────────────────────────┤
│  Functions Section                  │
│  - Magic (uint32)                   │
│  - Count (uint32)                   │
│  - Function List                    │
│    └─ Name (UTF-16LE, length flag)  │
│    └─ ID (uint32)                   │
│    └─ Reserved (uint32)             │
│    └─ VM Code Offset (uint32)       │
├─────────────────────────────────────┤
│  Labels Section                     │
│  - Count (uint32)                   │
│  - Label List                       │
│    └─ Name (UTF-16LE, length flag)  │
│    └─ VM Code Offset (uint32)       │
├─────────────────────────────────────┤
│  VM Data Section                    │
│  - Length (uint32)                  │
│  - Data (UTF-16LE strings pool)     │
├─────────────────────────────────────┤
│  VM Code Section                    │
│  - Length (uint32)                  │
│  - Bytecode Instructions            │
├─────────────────────────────────────┤
│  Strings Section                    │
│  - Count (uint32)                   │
│  - Range Table                      │
│    └─ Start (int32)                 │
│    └─ Length (int32)                │
│  - Table Length (uint32)            │
│  - String Data (UTF-16LE)           │
└─────────────────────────────────────┘
还没完工，远古版本的exec.dat还是不能反编译，结构体动过了.
"""

from vm_parser import VMParser

with open(r"VisualNovel\Engine\Malie\decompile\old.dat", "rb") as f:
    data = f.read()

script = VMParser(data)
pass
