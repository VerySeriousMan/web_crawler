# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2024.12.05
Author: ZhangYuetao
File Name: bilibili.py
Update: 2025.06.20
"""

import os
import time

from yt_dlp import YoutubeDL
from selenium import webdriver
from selenium.webdriver.common.by import By

import utils
import config
from logger import logger

WEB_NAME = 'bilibili'

basic_setting = config.load_config(config.BASIC_SETTING_PATH, config.BASIC_SETTING_DEFAULT_CONFIG)
save_path = basic_setting["save_path"]
type_name = basic_setting["type_name"]

VIDEO_IDX = config.get_idx(WEB_NAME, type_name, 'videos')

USED_VIDEO_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'))

utils.begin_logger(WEB_NAME, save_path, type_name, 
                   video_idx=VIDEO_IDX, 
                   used_video_urls=USED_VIDEO_URLS)


def add_idx():
    """
    增加视频索引。
    """
    global VIDEO_IDX
    VIDEO_IDX = VIDEO_IDX + 1


def get_video_pages(keyword, max_page=10, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    搜索bilibili页面链接。
    
    :param keyword: 搜索关键词。
    :param max_page: 最大搜索页数。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机 User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的 Chrome 浏览器。
    :param need_load: 是否需要手动登录页面。
    :return: 搜索到的页面链接列表。
    """
    options = utils.create_option(random_proxy, random_user_agent, headless, use_open_chrome)
    
    driver = webdriver.Chrome(options=options)

    if need_load:
        logger.info("需要手动登录页面")
        # 加载登录页面
        driver.get('https://www.bilibili.com/')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")
        
    video_urls = set()

    for i in range(max_page):
        search_url = f"https://search.bilibili.com/video?keyword={keyword}&from_source=webtop_search&duration=1&page={i + 1}&o={i * 36}"

        driver.get(search_url)
        time.sleep(3)

        post_links = driver.find_elements(By.CSS_SELECTOR, "div.bili-video-card__info--right")
        for link in post_links:
            a_tag = link.find_element(By.CSS_SELECTOR, "a")
            page = a_tag.get_attribute("href")
            video_urls.add(page)

        logger.info(f"第{i + 1}页找到{len(post_links)}个视频")

    video_urls = list(video_urls)
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'), video_urls)
    logger.info(f"爬取页面完成，共{len(video_urls)}个URL")
    
    driver.get('https://www.baidu.com')

    return video_urls


def download_videos(urls, save_path, retries=3):
    """
    下载指定的 B 站视频 URL 到本地指定路径。
    
    :param urls: B 站视频的网页地址列表。
    :param save_path: 保存视频的文件夹路径。
    :param retries: 重试次数。
    """
    os.makedirs(save_path, exist_ok=True)
    
    if not urls:
        logger.warning('urls empty')
        return
    
    old_video_idx = VIDEO_IDX
    
    for url in urls:
        download_bilibili_video(url, save_path, retries)
        
    config.update_idx(WEB_NAME, type_name, 'videos', VIDEO_IDX)

    logger.info(f"下载全部完成，本次共下载{VIDEO_IDX-old_video_idx}个视频（新计数值，VIDEO_IDX={VIDEO_IDX})")


def check_formats(video_url):
    """
    检查指定的 B 站视频 URL 的格式。
    
    :param video_url: B 站视频的网页地址。
    """
    ydl_opts = {
        'quiet': False,  # 显示信息
        'force_generic_extractor': True,  # 强制使用通用提取器
        'listformats': True,  # 获取视频的所有格式
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(video_url)


def download_bilibili_video(video_url, save_path, retries=3):
    """
    从指定的 B 站视频 URL 下载视频（指定画质，无音频）到本地指定路径。

    :param video_url: B 站视频的网页地址。
    :param save_path: 保存视频的文件夹路径。
    :param retries: 重试次数。
    """
    if not video_url:
        logger.info('empty！')
        return

    if video_url in USED_VIDEO_URLS:
        logger.info(f"视频链接 {video_url} 已经处理过，跳过下载。")
        return
    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)

    current_time = utils.get_formatted_timestamp()
    filename = f'{type_name[0].upper()}_blbl{VIDEO_IDX:05d}_{current_time}_RGB.mp4'

    # 配置 yt_dlp 的参数
    ydl_opts = {
        'format': 'mp4[height<=1080]',  # 选择画质
        'outtmpl': os.path.join(save_path, filename),  # 输出文件名格式
        'noplaylist': True,  # 如果是播放列表，下载第一个视频
        'quiet': False,  # 显示下载进度
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'  # 确保视频输出为 MP4 格式
        }],
        'postprocessor_args': [
            '-an'  # 去除音频
        ],
        'cookiefile': config.BILIBILI_COOKIE_PATH
    }

    for attempt in range(retries):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'), [video_url])
            USED_VIDEO_URLS.add(video_url)
            add_idx()
                
            logger.info(f"视频已成功下载到：{save_path}")
            break
        except Exception as e:
            logger.warning(f"尝试 {attempt + 1}/{retries} 失败: {e}")
    else:
        logger.error(f"所有尝试均失败，无法下载视频 {video_url}。")

def run(keywords, save_dir, max_pages=10, retries=3, random_proxy=False, random_user_agent=False, 
        headless=False, use_open_chrome=False, need_load=False, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param keywords: 关键词列表。
    :param save_dir: 保存路径。
    :param max_pages: 最大抓取页数。
    :param retries: 重试次数。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的Chrome浏览器。
    :param need_load: 是否需要手动登录页面。
    :param have_urls: 是否已经获取过视频链接。
    """
    os.makedirs(save_dir, exist_ok=True)
    
    old_video_idx = VIDEO_IDX

    for keyword in keywords:
        logger.info(f'========== 开始处理关键词: {keyword} ==========')
        try:
            if have_urls:
                video_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'))
            else:
                video_urls = get_video_pages(keyword, max_pages, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
                need_load = False  # 下次搜索时不需要加载登录页面
            
            if not video_urls:
                logger.warning(f"关键词[{keyword}]未提取到有效资源，跳过。")
                continue

            download_videos(video_urls, save_dir, retries)
        except Exception as e:
            logger.error(f"[关键词: {keyword}] 抓取失败: {e}")
        logger.info(f'========== 完成关键词: {keyword} ==========')
    
    utils.end_logger(WEB_NAME, save_dir, type_name, 
                     video_idx=VIDEO_IDX,
                     new_video_count=VIDEO_IDX-old_video_idx,)
        