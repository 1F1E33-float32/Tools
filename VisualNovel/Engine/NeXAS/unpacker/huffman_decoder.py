from typing import Optional

import numpy as np


class HuffmanNode:
    def __init__(self):
        self.symbol: Optional[int] = None
        self.left_node: Optional[HuffmanNode] = None
        self.right_node: Optional[HuffmanNode] = None


class HuffmanDecoder:
    def __init__(self, buffer: bytes):
        self._buffer = np.frombuffer(buffer, dtype=np.uint8)
        self._buffer_size = len(self._buffer)
        self._bit_count = 0
        self._byte_count = 0
        self._cur_value = 0
        self._root: Optional[HuffmanNode] = None

    def get_bits(self, need_bit: int) -> int:
        result = 0

        while need_bit > 0:
            if self._bit_count == 0:
                if self._byte_count >= self._buffer_size:
                    return 0
                self._cur_value = int(self._buffer[self._byte_count])
                self._byte_count += 1
                self._bit_count = 8

            read_bit = min(need_bit, self._bit_count)

            result <<= read_bit
            result |= self._cur_value >> (self._bit_count - read_bit)
            self._cur_value &= (1 << (self._bit_count - read_bit)) - 1

            self._bit_count -= read_bit
            need_bit -= read_bit

        return result

    def parse_bitstream_to_huffman_tree(self):
        node_stack = []

        self._root = HuffmanNode()
        node_stack.append(self._root)

        cur_node = node_stack[-1]

        while node_stack:
            if self.get_bits(1):
                # 创建新节点
                if cur_node.left_node is None:
                    node_stack.append(cur_node)
                    cur_node.left_node = HuffmanNode()
                    cur_node = cur_node.left_node
                else:
                    node_stack.append(cur_node)
                    cur_node.right_node = HuffmanNode()
                    cur_node = cur_node.right_node
            else:
                # 叶子节点，读取符号
                cur_node.symbol = self.get_bits(8)

                cur_node = node_stack[-1]
                node_stack.pop()

                if cur_node.right_node is None:
                    cur_node.right_node = HuffmanNode()
                    cur_node = cur_node.right_node

    def decode(self, decode_buffer_size: int) -> bytes:
        self.parse_bitstream_to_huffman_tree()

        decode_buffer = np.zeros(decode_buffer_size, dtype=np.uint8)
        decode_count = 0

        cur_node = self._root

        while decode_count < decode_buffer_size:
            # 根据比特值遍历树
            if self.get_bits(1) == 0:
                cur_node = cur_node.left_node
            else:
                cur_node = cur_node.right_node

            # 到达叶子节点
            if cur_node.left_node is None and cur_node.right_node is None:
                decode_buffer[decode_count] = cur_node.symbol
                decode_count += 1
                cur_node = self._root

        return decode_buffer.tobytes()
