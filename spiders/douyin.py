# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2024.12.06
Author: ZhangYuetao
File Name: douyin.py
Update: 2025.06.20
"""

import os
import re
import time
import random

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import unquote, parse_qs, urlparse

import utils
import config
from logger import logger

WEB_NAME = 'douyin'

basic_setting = config.load_config(config.BASIC_SETTING_PATH, config.BASIC_SETTING_DEFAULT_CONFIG)
save_path = basic_setting["save_path"]
type_name = basic_setting["type_name"]

VIDEO_IDX = config.get_idx(WEB_NAME, type_name, 'videos')

USED_VIDEO_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'))
USED_PAGE_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'))

utils.begin_logger(WEB_NAME, save_path, type_name, 
                   video_idx=VIDEO_IDX, 
                   used_video_urls=USED_VIDEO_URLS, used_page_urls=USED_PAGE_URLS)


def add_idx():
    """
    增加视频索引。
    """
    global VIDEO_IDX
    VIDEO_IDX = VIDEO_IDX + 1


def search_douyin_pages(keyword, max_scroll=10, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    搜索抖音视频页面链接。
    
    :param keyword: 搜索关键词。
    :param max_scroll: 最大滚动次数。
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
        driver.get('https://www.douyin.com')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")
    
    all_urls = set()

    # 加载搜索页面
    search_url = f'https://www.douyin.com/search/{keyword}?type=general'
    driver.get(search_url)

    time.sleep(5)

    video_xpath = "/html/body/div[2]/div/div/div/div/div[1]/div[1]/div[1]/div/div/span[2]"

    try:
        video_button = driver.find_element(By.XPATH, video_xpath)
        video_button.click()
        logger.info("成功点击 '视频' 按钮。")
    except Exception as e:
        logger.error("点击 '视频' 按钮失败:", e)
        return []

    time.sleep(5)

    last_height = driver.execute_script("return document.body.scrollHeight")

    for _ in range(max_scroll):
        # 模拟滚动到页面底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # 等待加载更多内容

        # 获取当前页面内容
        html = driver.page_source

        # 使用正则表达式查找 URL
        pattern = r'href="([^"]+)"'
        matches = re.findall(pattern, html)

        for match in matches:
            if 'www.douyin.com/video' in match:
                url = 'https:' + match
                light_url = url.replace('video', 'light')
                all_urls.add(light_url)

        # 检查是否到底
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            logger.info("已滚动到页面底部，停止滚动。")
            break
        last_height = new_height

    all_urls = list(all_urls)
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'), all_urls)
    logger.info(f"获取到 {len(all_urls)} 条 URL。")
    
    driver.get('https://www.baidu.com')

    return all_urls


def get_video_urls(page_urls, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False):
    """
    获取视频链接。
    
    :param page_urls: 页面URL列表。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机 User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的 Chrome 浏览器。
    :return: 视频url列表。
    """
    options = utils.create_option(random_proxy, random_user_agent, headless, use_open_chrome)
    driver = webdriver.Chrome(options=options)
    
    video_urls = []

    for page_url in page_urls:
        if page_url in USED_PAGE_URLS:
            logger.info(f"链接 {page_url} 已经处理过，跳过下载。")
            continue
        
        driver.get(page_url)
        time.sleep(float(round(random.uniform(4, 6), 1)))

        page_html = driver.page_source

        video_links = re.findall(r'https://[^\s"]+', page_html)
        url_list = []

        for link in video_links:
            if "v3-web.douyinvod.com" in link:
                url_list.append(link)

        if url_list:
            url = get_highest_br_video_url(url_list)

            logger.info(f"get_url:{url}")
            video_urls.append(url)

        else:
            logger.warning(f"获取失败：{page_url}")
        
        utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'), [page_url])
        USED_PAGE_URLS.add(page_url)

    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'), video_urls)
    logger.info(f"共获取 {len(video_urls)} 条视频URL")
    
    driver.get('https://www.baidu.com')

    return video_urls


def unescape_url(url):
    """
    将URL中的\u0026转义为&。
    
    :param url: 待转义的URL。
    :return: 转义后的URL。
    """
    return url.replace('\\u0026', '&')


def is_video_url(url):
    """
    检查URL是否包含视频标志。
    
    :param url: 待检查的URL。
    :return: True 如果包含视频标志，False 否则。
    """
    video_flags = ['video_mp4', 'media-video', 'tos-cn-ve-', 'hvc1']
    return any(flag in url.lower() for flag in video_flags)


def get_br_value(url):
    """
    从URL中提取br参数值（码率），返回整数。
    
    :param url: 待提取的URL。
    :return: br参数值。
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    br_values = query_params.get('br', [0])
    return int(br_values[0])  # 返回第一个br值（通常只有一个）


def get_highest_br_video_url(url_list):
    """
    获取br值最高的视频URL。
    
    :param url_list: 包含视频URL的列表。
    :return: br值最高的视频URL。
    """
    max_br = -1
    best_url = None

    for url in url_list:
        # 转义处理
        if '\\u0026' in url:
            url = unescape_url(url)

        # 解码URL编码字符
        url = unquote(url)

        # 只处理视频URL
        if is_video_url(url):
            br = get_br_value(url)
            if br > max_br:
                max_br = br
                best_url = url

    return best_url


def download_videos(video_infos, save_dir):
    """
    解析并下载全部视频。

    :param video_infos: 视频url列表。
    :param save_dir: 保存路径。
    """
    os.makedirs(save_dir, exist_ok=True)
    
    if not video_infos:
        logger.warning('urls empty')
        return

    old_idx = VIDEO_IDX

    for video_info in video_infos:
        download_douyin_video(video_info, save_dir)
    
    config.update_idx(WEB_NAME, type_name, 'videos', VIDEO_IDX)

    logger.info(f"下载全部完成，本次共下载{VIDEO_IDX - old_idx}个视频（新计数值，VIDEO_IDX={VIDEO_IDX})")


def download_douyin_video(video_url, save_dir):
    """
    下载单个视频。

    :param video_url: 视频url。
    :param save_dir: 保存路径。
    """
    if not video_url:
        logger.info('empty！')
        return

    if video_url in USED_VIDEO_URLS:
        logger.info(f"视频链接 {video_url} 已经处理过，跳过下载。")
        return

    for _ in range(5):
        header = {
                'User-Agent': utils.get_random_user_agent(),
                'Referer': 'https://www.douyin.com/',  # 设置Referer
            }
        proxy = utils.get_random_proxy()
        
        try:
            response = requests.get(video_url, headers=header, proxies={'https': proxy}, stream=True, timeout=60)
            response.raise_for_status()  # 如果请求失败，抛出异常

            current_time = utils.get_formatted_timestamp()

            filename = f'{type_name[0].upper()}_douyin{VIDEO_IDX:05d}_{current_time}_RGB.mp4'

            save_path = os.path.join(save_dir, filename)

            # 将视频内容写入文件
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)

            utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'), [video_url])
            USED_VIDEO_URLS.add(video_url)
            add_idx()

            logger.info(f"视频已成功下载到 {save_path}")
            break
        except Exception as e:
            logger.error(f"{proxy}:下载失败: {e}")
            continue


def process_batch(batch, save_dir):
    """
    处理批次数据。
    
    :param batch: 批次数据。
    :param save_dir: 保存路径。
    """
    # 处理每批数据
    logger.info(f"Processing batch: {batch}")
    video_urls = get_video_urls(batch)

    download_videos(video_urls, save_dir)


def process_list_in_batches(page_urls, save_dir, batch_size=100):
    """
    将获取的页面url列表按照指定大小的批次进行处理（处理大批量下临时链接过期问题）。
    
    :param page_urls: 获取的页面url列表。
    :param save_dir: 保存路径。
    :param batch_size: 批次大小。
    """
    os.makedirs(save_dir, exist_ok=True)
    # 计算总共有多少批
    total_batches = (len(page_urls) + batch_size - 1) // batch_size

    for i in range(total_batches):
        # 获取当前批次的切片
        start_index = i * batch_size
        end_index = start_index + batch_size
        batch = page_urls[start_index:end_index]

        # 处理当前批次
        process_batch(batch, save_dir)


def run(keywords, save_dir, max_scroll=10, batch_size=0, random_proxy=False, random_user_agent=False, 
        headless=False, use_open_chrome=False, need_load=False, have_pages=False, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param keywords: 关键词列表。
    :param save_dir: 保存路径。
    :param max_scroll: 最大滚动次数。
    :param batch_size: 多批次处理的批次大小（默认为0，不开启多批次处理）。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的Chrome浏览器。
    :param need_load: 是否需要手动登录页面。
    :param have_pages: 是否已经获取过页面链接。
    :param have_urls: 是否已经获取过视频链接。
    """
    os.makedirs(save_dir, exist_ok=True)
    
    old_video_idx = VIDEO_IDX

    for keyword in keywords:
        logger.info(f'========== 开始处理关键词: {keyword} ==========')
        try:
            if have_pages:
                pages = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'))
            else:
                pages = search_douyin_pages(keyword, max_scroll, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
                need_load = False  # 下次搜索时不需要加载登录页面
                
            if not pages:
                logger.warning(f"关键词[{keyword}]未获取到有效页面链接，跳过。")
                continue
            
            if batch_size > 0:
                # 多批次处理
                process_list_in_batches(pages, save_dir, batch_size)
            else:
                # 单批次处理
                if have_urls:
                    video_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'))
                else:
                    video_urls = get_video_urls(pages, random_proxy, random_user_agent, headless, use_open_chrome)
                
                if not video_urls:
                    logger.warning(f"关键词[{keyword}]未提取到有效资源，跳过。")
                    continue

                download_videos(video_urls, save_dir)
        except Exception as e:
            logger.error(f"[关键词: {keyword}] 抓取失败: {e}")
        logger.info(f'========== 完成关键词: {keyword} ==========')
        
    utils.end_logger(WEB_NAME, save_dir, type_name, 
                     video_idx=VIDEO_IDX,
                     new_video_count=VIDEO_IDX-old_video_idx)
        