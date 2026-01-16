import os
import shutil
import hashlib
import zipfile
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad
import os as crypto_os

def calculate_md5(file_path, chunk_size=4096):
    """计算文件的MD5哈希值"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def copy_item_with_md5_dedup(source_item, destination):
    """复制单个文件或文件夹到目标路径，并进行MD5去重"""
    item_name = os.path.basename(source_item)
    dest_path = os.path.join(destination, item_name)
    
    if os.path.isdir(source_item):
        os.makedirs(dest_path, exist_ok=True)
        for sub_item in os.listdir(source_item):
            sub_source = os.path.join(source_item, sub_item)
            copy_item_with_md5_dedup(sub_source, dest_path)
    else:
        if os.path.exists(dest_path):
            source_md5 = calculate_md5(source_item)
            dest_md5 = calculate_md5(dest_path)
            
            if source_md5 != dest_md5:
                shutil.copy2(source_item, dest_path)
                print(f"已覆盖不同版本的文件: {dest_path}")
            else:
                print(f"文件相同，已跳过: {dest_path}")
        else:
            shutil.copy2(source_item, dest_path)
            print(f"已复制文件: {dest_path}")

def copy_multiple_sources(source_paths, destination):
    """处理多个源路径，复制到同一个目标文件夹"""
    os.makedirs(destination, exist_ok=True)
    
    for source in source_paths:
        if not os.path.exists(source):
            print(f"警告: 源路径不存在，已跳过 - {source}")
            continue
        print(f"\n开始处理源路径: {source}")
        copy_item_with_md5_dedup(source, destination)

def zip_directory(folder_path, zip_path):
    """将文件夹压缩为ZIP文件"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    print(f"已将文件夹压缩为: {zip_path}")
    return zip_path

def encrypt_file(input_file, output_file, password):
    """使用AES加密文件"""
    # 生成密钥和IV
    salt = crypto_os.urandom(16)
    key = PBKDF2(password, salt, dkLen=32, count=1000000)  # 32字节密钥用于AES-256
    iv = crypto_os.urandom(16)  # 16字节IV用于AES
    
    # 初始化加密器
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # 读取并加密文件内容
    with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        # 先写入salt和iv（解密时需要）
        f_out.write(salt)
        f_out.write(iv)
        
        # 分块加密
        while True:
            chunk = f_in.read(4096)
            if len(chunk) == 0:
                break
            elif len(chunk) % 16 != 0:
                chunk = pad(chunk, AES.block_size)  # 填充到块大小
            
            f_out.write(cipher.encrypt(chunk))
    
    print(f"文件已加密: {output_file}")
    return output_file
def on_backup(source_paths, destination):
    # 创建单独的文件夹来存储备份文件，以免与其他文件混淆
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = os.path.join(destination, f"backup_{timestamp}")
    if not os.path.exists(destination):
        os.mkdir(destination)

    copy_multiple_sources(source_paths, destination)
    print("\n所有源路径处理完成")

    # 备份完成后创建压缩包，文件名包含时间戳
    zip_filename = f"backup_{timestamp}.zip"
    zip_path = os.path.join(os.path.dirname(destination), zip_filename)
    
    print("\n开始压缩文件夹...")
    zip_path = zip_directory(destination, zip_path)

    #  # 加密压缩包
    # encrypted_zip_path = zip_path + ".encrypted"
    # encryption_password = "liuguosong"  # 建议使用更复杂的密码
    # # 实际应用中建议通过输入获取密码，而不是硬编码
    # # encryption_password = input("请输入加密密码: ")
    
    # print("\n开始加密压缩包...")
    # encrypt_file(zip_path, encrypted_zip_path, encryption_password)
    
    # # 可选：删除原始未加密的压缩包
    # os.remove(zip_path)
    # print(f"已删除原始压缩包: {zip_path}")
    
    # print("加密压缩完成")
