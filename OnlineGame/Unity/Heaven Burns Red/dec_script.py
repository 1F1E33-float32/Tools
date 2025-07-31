import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

def decrypt_aes_base64(base64_data, key, iv):
    cipher_data = b64decode(base64_data)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(cipher_data), AES.block_size)
    return decrypted_data

def decrypt_files(input_folder, output_folder, key, iv):
    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith(".bytes"):
                input_file_path = os.path.join(root, filename)

                try:
                    with open(input_file_path, 'rb') as file:
                        file_content = file.read()
                    base64_data = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    print(f"文件 {filename} 不是有效的 UTF-8 编码，跳过该文件。")
                    continue

                try:
                    decrypted_data = decrypt_aes_base64(base64_data, key, iv)
                    
                    # 保持目录结构
                    relative_path = os.path.relpath(input_file_path, input_folder)
                    output_file_path = os.path.join(output_folder, relative_path)
                    output_file_path = output_file_path.replace(".bytes", ".lua")
                    
                    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

                    with open(output_file_path, 'wb') as file:
                        file.write(decrypted_data)
                    print(f"解密并保存为 .lua 文件: {output_file_path}")
                except ValueError as e:
                    print(f"解密失败: {filename}, 错误信息: {str(e)}")

if __name__ == "__main__":
    input_folder = r"C:\Users\bfloat16\Desktop\hbr\TextAssets\Assets\Lua"
    output_folder = r"C:\Users\bfloat16\Desktop\hbr\TextAssets\Assets\Lua_dec"
    key = bytes([81, 103, 105, 88, 50, 97, 105, 33, 65, 35, 110, 98, 103, 58, 73, 111])
    iv = bytes([119, 124, 81, 113, 74, 48, 65, 82, 117, 77, 84, 37, 115, 85, 112, 114])
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    decrypt_files(input_folder, output_folder, key, iv)