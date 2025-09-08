class MyStr:
    """一个支持文件流操作的字节数据包装类"""
    
    def __init__(self, data):
        """初始化MyStr对象
        
        Args:
            data: 字节数据
        """
        self.data = data
        self.position = 0
        self.length = len(data)
    
    def __getitem__(self, key):
        """支持切片和索引操作"""
        return self.data[key]
    
    def read(self, size=-1):
        """读取指定数量的字节
        
        Args:
            size: 要读取的字节数，-1表示读取所有剩余字节
            
        Returns:
            读取的字节数据
        """
        if size == -1:
            result = self.data[self.position:]
            self.position = self.length
        else:
            result = self.data[self.position:self.position + size]
            self.position += size
        return result
    
    def seek(self, offset, whence=0):
        """设置文件指针位置
        
        Args:
            offset: 偏移量
            whence: 起始位置 (0=开头, 1=当前位置, 2=末尾)
        """
        if whence == 0:  # 从开头计算
            self.position = offset
        elif whence == 1:  # 从当前位置计算
            self.position += offset
        elif whence == 2:  # 从末尾计算
            self.position = self.length + offset
        
        # 确保位置在有效范围内
        self.position = max(0, min(self.position, self.length))
    
    def tell(self):
        """返回当前文件指针位置"""
        return self.position
    
    def __len__(self):
        """返回数据长度"""
        return self.length
