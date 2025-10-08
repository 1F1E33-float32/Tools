# Reference
https://github.com/YuriSizuku/GalgameReverse/tree/master/project/krkr

https://github.com/arcusmaximus/KirikiriTools/tree/master/KirikiriDescrambler

https://github.com/UlyssesWu/FreeMote

# Kirikiri2 / KirikiriZ
如果是`.ks`结尾的明文脚本，使用`parse_ks.py`解析ks，遇到新的模式请尝试自己补全或者开issue。

如果是`.ks.scn`结尾的PSB脚本，先运行`1_Scan_PSB.py`解压PSB，然后再运行`3_Parse_Scn.py`解析脚本，遇到新的模式请尝试自己补全或者开issue。

`999.py`只适用于[神罪降临 Uberich: Advent Sinners](https://store.steampowered.com/app/2323200/_Uberich_Advent_Sinners)的人名映射表生成。

# KiriKiriZ with cxdecv2
原始的流程是：游戏加载脚本 -> 解析脚本 -> 去封包内读取文件

cxdec的流程：游戏加载脚本 -> 解析脚本 -> 计算路径和文件名的hash（不可逆）-> 去封包内读取文件

但是可以用[KrkrExtractForCxdecV2](https://github.com/YeLikesss/KrkrExtractForCxdecV2)先拆出文件名为hash的文件，然后用`1_Scan_PSB.py`扫描解压PSB，用`2_Restore_ScnName.py`还原scn名称，最后用`3_Parse_Scn.py`解析scn并且生成一个文件列表，然后用项目里面的`caculate_cxdecv2_hash`hook住cxdec，往里面灌文件名来主动获取hash，运行`4_cxdec_Name.py`还原所有音频名称。