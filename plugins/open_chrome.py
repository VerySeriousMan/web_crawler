# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.06.13
Author: ZhangYuetao
File Name: open_chrome.py
Update: 2025.06.16
"""

import subprocess

import config


def run():
    """
    打开本地指定节点 Chrome 浏览器。
    """
    chrome_setting = config.load_config(config.CHROME_SETTING_PATH, config.CHROME_SETTING_DEFAULT_CONFIG)
    chrome_path = chrome_setting['chrome_path']
    user_data_dir = chrome_setting['user_data_dir'] 
    port = chrome_setting['port']

    cmd = [
        chrome_path,
        f'--remote-debugging-port={port}',
        f'--user-data-dir={user_data_dir}'
    ]

    # 启动 Chrome 浏览器
    subprocess.Popen(cmd)
