# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2024.12.13
Author: ZhangYuetao
File Name: proxy_test.py
Update: 2025.06.16
"""

import sys
import os
import time

import requests
import concurrent.futures
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 将父目录添加到导包路径

import config
import utils

"""
代理IP检测工具
功能：
1. 验证代理IP是否能用于目标网站
2. 检测HTTPS支持能力
3. 测量代理响应速度
4. 自动保存可用代理到文件
"""

# 配置区域 ================================================
TARGET_URL = "https://www.baidu.com"  # 实际爬取的目标页面
TIMEOUT = 30  # 单次请求超时时间（秒）
MAX_WORKERS = 20  # 并发检测线程数
PROXY_TYPE_WHITELIST = ['http', 'https', 'socks4', 'socks5']  # 允许的代理类型
OUTPUT_FILE = "usable_proxies.txt"
# ========================================================


def load_proxies():
    """
    加载代理列表，自动补充协议头。
    
    :return: 代理列表。
    """
    try:
        raw_proxies = utils.read_list_from_txt(config.PROXIES_PATH)

        processed = []
        for p in raw_proxies:
            if '://' not in p:
                processed.append(f"http://{p}")  # 默认补全HTTP协议

            else:
                processed.append(p)
        return list(set(processed))  # 去重
    except Exception as e:
        print(f"加载代理文件失败: {str(e)}")
        return []


def validate_proxy(proxy):
    """
    深度验证代理可用性。
    
    :param proxy: 代理IP地址。
    :return: 检测结果。
    """
    result = {
        "proxy": proxy,
        "usable": False,
        "response_time": None,
        "error": None,
        "status_code": None
    }

    parsed = urlparse(proxy)
    if parsed.scheme not in PROXY_TYPE_WHITELIST:
        result["error"] = f"非法协议类型: {parsed.scheme}"
        return result

    proxies = {
        "https": proxy
    }

    headers = {
        "User-Agent": utils.get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            start = time.time()
            response = requests.get(
                TARGET_URL,
                headers=headers,
                proxies=proxies,
                timeout=TIMEOUT,
                allow_redirects=False
            )
            latency = round(time.time() - start, 2)

            if response.status_code == 200:
                if "captcha" in response.text.lower():
                    result["error"] = "触发反爬验证"
                else:
                    result.update({"usable": True, "response_time": latency, "status_code": 200})
                    break
            else:
                result["error"] = f"HTTP状态码异常: {response.status_code}"

        except Exception as e:
            if attempt == max_retries - 1:
                result["error"] = str(e)
            continue  # 网络错误时继续重试

    return result


def save_results(proxies):
    """
    保存结果。
    
    :param proxies: 可用代理列表。
    """
    with open(OUTPUT_FILE, 'w') as f:
        for p in proxies:
            f.write(f"{p}\n")
    print(f"可用代理已保存至: {OUTPUT_FILE}")


def run():
    """
    主函数，调度接口。
    """
    print("=== 代理检测开始 ===")

    # 加载代理
    raw_proxies = load_proxies()
    if not raw_proxies:
        print("未找到有效代理地址")
        return
    print(f"共加载 {len(raw_proxies)} 个代理")

    # 并发检测
    usable_proxies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(validate_proxy, p): p for p in raw_proxies}

        for future in concurrent.futures.as_completed(futures):
            proxy = futures[future]
            try:
                result = future.result()
                if result["usable"]:
                    print(f"✅ 可用代理: {proxy} 响应时间: {result['response_time']}s")
                    usable_proxies.append(proxy)
                else:
                    print(f"❌ 不可用: {proxy} 原因: {result['error']}")
            except Exception as e:
                print(f"检测异常: {proxy} - {str(e)}")

    # 结果处理
    print(f"\n检测完成，可用代理数: {len(usable_proxies)}/{len(raw_proxies)}")
    if usable_proxies:
        print("可用代理列表:")
        for p in usable_proxies:
            print(f"  - {p}")
        save_results(usable_proxies)
    else:
        print("没有可用的代理")


if __name__ == "__main__":
    run()
