from vm_parser_old import VMParser as VMParser_old
from vm_parser_new import VMParser as VMParser_new

with open(r"C:\Users\bfloat16\Downloads\Soranica Ele\EXEC", "rb") as f:
    data = f.read()

#script = VMParser_old(data)
script = VMParser_new(data)
pass
