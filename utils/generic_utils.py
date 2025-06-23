# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2024.12.05
Author: ZhangYuetao
File Name: generic_utils.py
Update: 2025.06.20
"""

import ast
import os
import random
from datetime import datetime

import cv2
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options

import config
from logger import logger


def _get_user_agents():
    """
    获取默认UA列表。
    
    :return: UA列表。
    """
    try:
        with open(config.USER_AGENTS_PATH, "r", encoding='utf-8') as file:
            user_agents = [line.strip() for line in file if line.strip()]
        logger.info("成功获取User-Agent列表")
        
        return user_agents
    except FileNotFoundError:
        logger.error("User-Agent file not found.")
        
        return []


def get_random_user_agent():
    """
    获取随机UA。
    
    :return: 随机UA。
    """
    try:
        ua = UserAgent(platforms='desktop').random  # 获取随机UA,筛选为桌面设备
        logger.debug((f'使用随机UA: {ua}'))
    except Exception as e:
        logger.warning(f"UA生成失败,使用备用UA: {e}")  
        
        user_agents = _get_user_agents()
        ua = random.choice(user_agents)
        logger.debug((f'使用随机UA【备用】: {ua}'))
        
    return ua


def _get_proxies():
    """
    获取代理列表。
    
    :return: 代理列表。
    """
    try:
        with open(config.PROXIES_PATH, "r", encoding='utf-8') as file:
            proxies = [line.strip() for line in file if line.strip()]

        return proxies
    except FileNotFoundError:
        logger.error("Proxies file not found.")
        
        return []


def get_random_proxy():
    """
    获取随机代理。
    
    :return: 随机代理。
    """
    proxies = _get_proxies()
    logger.debug(f'使用随机代理: {proxies}')
    
    return random.choice(proxies) if proxies else None


def get_formatted_timestamp():
    """
    获取当前时间戳并格式化为 年_月_日_时_分_秒_毫秒 格式。

    return: 格式化后的时间戳字符串。
    """
    # 获取当前时间
    now = datetime.now()

    # 格式化时间戳
    formatted_timestamp = now.strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]  # 去掉微秒的最后三位

    return formatted_timestamp


def save_list_to_txt(txt_path, data_list):
    """
    将 list 存入 txt 文件，每个元素占一行。如果文件不存在则新建，存在则追加。

    :param txt_path: 保存的txt路径。
    :param data_list: 待保存的数据列表。
    """
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    mode = "a" if os.path.exists(txt_path) else "w"

    with open(txt_path, mode, encoding="utf-8") as f:
        for item in data_list:
            f.write(str(item) + "\n")


def read_list_from_txt(txt_path, parse=False):
    """从 txt 文件读取 list，可选解析数据结构

    :param txt_path: 读取的txt路径。
    :param parse: 是否解析数据，默认False。
    :return: 读取的list。
    """
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
        return [ast.literal_eval(line) for line in lines] if parse else lines


def check_video_type(video_path):
    """
    判断视频是 RGB 还是 IR（红外）。
    
    :param video_path: 视频路径。
    :return: 视频类型 ('RGB' 或 'IR')，如果出错则返回 None。
    """
    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.warning(f"判断视频类型失败，无法打开视频: {video_path}")
            return None

        ret, frame = cap.read()  # 读取第一帧
        
        if not ret:
            logger.warning(f"判断视频类型失败，无法读取视频帧: {video_path}")
            return None

        # 获取通道数
        if len(frame.shape) == 3:
            channels = frame.shape[2]
        else:
            channels = 1

        if channels == 3:
            return 'RGB'
        elif channels == 1:
            return 'IR'
        else:
            logger.warning(f"未知的视频通道数: {channels}，默认返回 RGB")
            return 'RGB'
            
    except Exception as e:
        logger.error(f"判断视频类型时发生异常: {str(e)}")
        return None
        
    finally:
        if cap is not None:
            cap.release()  # 释放资源


def create_option(random_user_agent=False, random_proxy=False, headless=False, use_open_chrome=False):
    """
    创建 Chrome 浏览器选项。
    
    :param random_user_agent: 是否使用随机 User-Agent。
    :param random_proxy: 是否使用随机代理。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的 Chrome 浏览器。
    :return: Chrome 浏览器选项。
    """
    options = Options()
    options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
    options.add_argument('--no-first-run')  # 跳过首次运行向导
    options.add_argument('--disable-blink-features=AutomationControlled')  # 反爬虫检测
    options.add_argument('--disable-background-networking')  # 禁用后台网络交互
    options.add_argument('--disable-sync')  # 关闭账号同步
    options.add_argument('--disable-extensions')  # 禁用扩展
    options.add_argument('--disable-default-apps')  # 禁用默认应用
    options.add_argument('--disable-translate')  # 禁用翻译
    options.add_argument('--disable-web-resources')  # 禁用网络资源加载
    options.add_argument('--disable-component-update')  # 禁用组件更新
    options.add_argument('--disable-domain-reliability')  # 禁用域名可靠性检测
    options.add_argument('--disable-notifications')  # 禁用通知
    options.add_argument('--disable-features=TranslateUI')  # 关闭翻译 UI
    options.add_argument('--no-sandbox')  # 以 root 运行
    options.add_argument('--disable-dev-shm-usage')  # 共享内存不足时避免崩溃
    options.add_argument('--log-level=3')  # 只显示严重错误，减少日志
    
    if random_proxy:
        options.add_argument(f'--proxy-server={get_random_proxy()}')
        logger.info("启用随机代理")
    if random_user_agent:
        options.add_argument(f'--user-agent={get_random_user_agent()}')
        logger.info("启用随机 User-Agent")

    if headless:
        options.add_argument('--headless')  # 无界面模式
        options.add_argument('--disable-gpu')
        logger.info("启用无头模式")

    if use_open_chrome:
        chrome_setting = config.load_config(config.CHROME_SETTING_PATH, config.CHROME_SETTING_DEFAULT_CONFIG)
        port = chrome_setting['port']
        address = f"127.0.0.1:{port}"
        options.debugger_address = address
        logger.info(f"成功连接到已打开的 Chrome 浏览器 :{address}")

    return options
