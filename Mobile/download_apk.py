#!/usr/bin/env python3
"""
从 Hugging Face 下载 APK 文件
使用前请安装：pip install requests tqdm
"""

import requests
from tqdm import tqdm
import os

# ========== 配置区域（请修改为你的实际信息）==========
REPO_ID = "你的用户名/你的仓库名"          # 例如 "ace-trump-tech/DeltaForce-OBS-Locker"
FILENAME = "Locker_Android.apk"           # 要下载的文件名
# 如果文件在某个子目录下，例如 "apk/Locker_Android.apk"，则写 "apk/Locker_Android.apk"
# ===================================================

def download_file_from_hf(repo_id, filename, local_path=None):
    """从 Hugging Face 下载文件"""
    if local_path is None:
        local_path = filename

    # Hugging Face 的原始文件下载 URL 格式
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    print(f"正在从 {url} 下载...")
    response = requests.get(url, stream=True)
    
    if response.status_code != 200:
        print(f"下载失败，HTTP 状态码: {response.status_code}")
        print("请检查 REPO_ID 和 FILENAME 是否正确，且仓库是公开的。")
        return False
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(local_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
    
    print(f"下载完成: {local_path}")
    return True

if __name__ == "__main__":
    success = download_file_from_hf(REPO_ID, FILENAME)
    if not success:
        exit(1)
