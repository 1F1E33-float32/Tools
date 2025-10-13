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
还没完工，只能正确反编译老版本的exec.dat，新版本把一个page作为一个字符串了。
"""

from vm_parser import VMParser

with open(r"C:\Users\bfloat16\Desktop\MalieScriptEditor\malie_decompiler\old.dat", "rb") as f:
    data = f.read()

script = VMParser(data)
pass
