# PyCriCodecs
魔改版，只能解析+解压acb和awb容器内的hca，并且还原原始文件名；以及把chip1和chip56加密的hca解密成chip0，然后用libavcodec解码hca。

acb的CUE UTF表映射参考自：https://github.com/vgmstream/vgmstream/blob/d4f9a6f43cbf696dd48d3b9c0f1a8b28f01114e4/src/meta/acb.c#L1017

hca的解密参考自：https://github.com/vgmstream/vgmstream/blob/d4f9a6f43cbf696dd48d3b9c0f1a8b28f01114e4/src/coding/libs/clhca.c#L492