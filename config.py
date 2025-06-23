# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.06.09
Author: ZhangYuetao
File Name: config.py
Update: 2025.06.16
"""

import os

import toml

GOOGLE_API_KEY = "AIzaSyDNvWCflhZWROuxilCWar9Hi_Iym77DmOc"

USER_AGENTS_PATH = 'settings/lake/user_agents.txt'
PROXIES_PATH = 'settings/lake/proxies.txt'

USED_URLS_DIR_PATH = 'history'
LOG_FOLDER_PATH = 'logs'

BASIC_SETTING_PATH = 'settings/basic_setting.toml'
CHROME_SETTING_PATH = 'settings/chrome_setting.toml'
LOAD_COOKIES_PATH = 'settings/cookies/load_cookies.toml'

BILIBILI_COOKIE_PATH = 'settings/cookies/www.bilibili_com.txt'

BASIC_SETTING_DEFAULT_CONFIG = {
    'save_path': 'download',
    'type_name': 'cat',
}

LOAD_COOKIES_DEFAULT_CONFIG = {
    'baidutieba_cookie': '',
    'bilibili_cookie': '',
    'douyin_cookie': '',
    'sunny_door_cookie': '',
}

CHROME_SETTING_DEFAULT_CONFIG = {
    'chrome_path': '',
    'user_data_dir': '',
    'port': '9222',
}


def load_config(filepath, default):
    """
    加载配置文件，如果文件不存在或解析失败则使用默认配置。

    :param filepath: TOML 文件路径。
    :param default: 默认配置字典。
    :return: 加载的配置字典。
    """
    # 尝试读取现有的 TOML 文件
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                config = toml.load(f)
        else:
            config = default
    except (FileNotFoundError, toml.TomlDecodeError):
        config = default

    # 检查是否缺少必要的参数，如果缺少则更新为默认值
    for key, value in default.items():
        if key not in config:
            config[key] = value

    return config


def save_config(file_path, config_dict):
    """
    将配置字典保存到 TOML 文件中。

    :param file_path: TOML 文件路径。
    :param config_dict: 配置字典。
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        toml.dump(config_dict, f)


def get_save_history_path(web_name, type_name, way='get', format='images'):
    """
    获取保存历史记录的文件路径。

    :param web_name: 网站名称。
    :param type_name: 类型名称。
    :param way: 获取方式。
    :param format: 文件格式。
    :return: 文件路径。
    """
    txt_name = f'{way}_{format}.txt'
    dir_path = os.path.join(USED_URLS_DIR_PATH, web_name, type_name)
    os.makedirs(dir_path, exist_ok=True)
    
    return os.path.join(dir_path, txt_name)


def init_used_urls(used_txt_path):
    """
    初始化已使用的 URL 集合。

    :param used_txt_path: 已使用的 URL 文件路径。
    :return: 已使用的 URL 集合(不存在则返回空集合)。
    """
    try:
        with open(used_txt_path, 'r') as url_file:
            return set(url.strip() for url in url_file.readlines())
    except FileNotFoundError:
        # 如果文件不存在，创建一个空的集合
        return set()


def get_idx(web_name, type_name, format='images'):
    """
    获取已使用的 URL 的索引值。

    :param web_name: 网站名称。
    :param type_name: 类型名称。
    :param format: 文件格式。
    :return: 已使用的 URL 的索引值。
    """
    idx_path = os.path.join(USED_URLS_DIR_PATH, web_name, type_name, f'{format}_idx.txt')
    try:
        if os.path.exists(idx_path):
            with open(idx_path, 'r') as f:
                return int(f.read())
        else:
            return 0
    except Exception as e:
        print(f"获取已使用的 URL 的索引值失败：{e}")
        return 0


def update_idx(web_name, type_name, format='images', idx=0):
    """
    更新已使用的 URL 的索引值。

    :param web_name: 网站名称。
    :param type_name: 类型名称。
    :param format: 文件格式。
    :param idx: 新的索引值。
    """
    idx_path = os.path.join(USED_URLS_DIR_PATH, web_name, type_name, f'{format}_idx.txt')
    with open(idx_path, 'w') as f:
        f.write(str(idx))
