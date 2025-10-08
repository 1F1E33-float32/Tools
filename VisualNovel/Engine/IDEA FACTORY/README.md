# Reference
https://github.com/robbie01/stcm2-asm

# 新版引擎（函数调用）
1. 先写特征码：SPEAKER.txt，TEXT.txt，VOICE.txt，COMBINE.txt（voice和text在同一行的情况）
2. 跑`scan_seq.py`扫描出对应的函数，然后把结果复制到`parse_new.py`最前面。
3. 跑`parse_new.py`生成index.json
4. 跑`File_diff.py`看有哪些voice不在index.json里面，全局搜索几个voice看看，如果确实没有可以不管，一般来说会有500左右的voice脚本里面搜不到。