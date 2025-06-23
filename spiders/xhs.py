# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2024.12.06
Author: ZhangYuetao
File Name: xhs.py
Update: 2025.06.20
"""

import os
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
import requests

import utils
import config
from logger import logger

WEB_NAME = 'xhs'

basic_setting = config.load_config(config.BASIC_SETTING_PATH, config.BASIC_SETTING_DEFAULT_CONFIG)
save_path = basic_setting["save_path"]
type_name = basic_setting["type_name"]

VIDEO_IDX = config.get_idx(WEB_NAME, type_name, 'videos')
IMAGE_IDX = config.get_idx(WEB_NAME, type_name, 'images')

USED_VIDEO_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'))
USED_IMAGE_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'images'))
USED_PAGE_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'))

utils.begin_logger(WEB_NAME, save_path, type_name, 
                   video_idx=VIDEO_IDX, image_idx=IMAGE_IDX,
                   used_video_urls=USED_VIDEO_URLS, used_image_urls=USED_IMAGE_URLS, used_page_urls=USED_PAGE_URLS)


def add_video_idx():
    """
    增加视频索引。
    """
    global VIDEO_IDX
    VIDEO_IDX = VIDEO_IDX + 1


def add_image_idx():
    """
    增加图片索引。
    """
    global IMAGE_IDX
    IMAGE_IDX = IMAGE_IDX + 1


def search_xhs_pages(keyword, max_scroll=10, save_way=0, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    搜索小红书页面链接。
    
    :param keyword: 搜索关键词。
    :param max_scroll: 最大滚动次数。
    :param save_way: 保存方式（0=全部，1=仅视频，2=仅图片）。
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
        driver.get('https://www.xiaohongshu.com/login')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")

    # 加载搜索页面
    search_url = f'https://www.xiaohongshu.com/search_result/?keyword={keyword}'
    
    video_xpath = "/html/body/div[2]/div[1]/div[2]/div[2]/div/div[1]/div[1]/div/div/div[3]"
    image_xpath = "/html/body/div[2]/div[1]/div[2]/div[2]/div/div[1]/div[1]/div/div/div[2]"
    
    all_urls = set()

    # 爬取视频
    if save_way == 0  or save_way == 1:
        try:
            driver.get(search_url)

            time.sleep(5)
            
            video_button = driver.find_element(By.XPATH, video_xpath)
            video_button.click()
            logger.info("成功点击 '视频' 按钮。")
        except Exception as e:
            logger.error("点击 '视频' 按钮失败,提前退出，返回空列表", e)
            # driver.quit()

            return []

        time.sleep(5)
        
        last_height = driver.execute_script("return document.body.scrollHeight")

        for _ in range(max_scroll):
            # 模拟滚动到页面底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 等待加载更多内容

            # 获取当前页面内容
            html = driver.page_source

            # 使用正则表达式查找 URL
            pattern = r'href="([^"]+)"'
            matches = re.findall(pattern, html)

            for match in matches:
                if '/search_result/' in match:
                    url = 'https://www.xiaohongshu.com' + match
                    all_urls.add(url)

            # 检查是否到底
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("已滚动到页面底部，停止滚动。")
                break
            last_height = new_height

    # 爬取图片
    if save_way == 0 or save_way == 2:
        try:
            driver.get(search_url)

            time.sleep(5)
            
            image_button = driver.find_element(By.XPATH, image_xpath)
            image_button.click()
            logger.info("成功点击 '图文' 按钮。")
        except Exception as e:
            logger.error("点击 '图文' 按钮失败:", e)
            return []

        time.sleep(5)

        last_height = driver.execute_script("return document.body.scrollHeight")

        for _ in range(max_scroll):
            # 模拟滚动到页面底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 等待加载更多内容

            # 获取当前页面内容
            html = driver.page_source

            # 使用正则表达式查找 URL
            pattern = r'href="([^"]+)"'
            matches = re.findall(pattern, html)

            for match in matches:
                if '/search_result/' in match:
                    url = 'https://www.xiaohongshu.com' + match
                    all_urls.add(url)

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


def get_xhs_urls(all_urls):
    """
    获取视频和图片链接。
    
    :param all_urls: 页面URL列表。
    :return: 视频url列表，图片url列表。
    """
    image_urls = []
    video_urls = []
    
    for note_url in all_urls:
        if note_url in USED_PAGE_URLS:
            logger.info(f"笔记链接 {note_url} 已经处理过，跳过下载。")
            continue
        
        for _ in range(5):
            try:
                logger.info(f'begin{note_url}')
                
                headers = {
                    'User-Agent': utils.get_random_user_agent(),
                    'Referer': 'https://www.xiaohongshu.com/',  # 设置Referer
                }

                proxy = utils.get_random_proxy()

                response = requests.get(note_url, headers=headers, proxies={'https': proxy}, timeout=10)
                response.raise_for_status()

                html = response.text

                pattern_image = r'<meta name="og:image" content="([^"]+)"'
                pattern_video = r'<meta name="og:video" content="([^"]+)"'
                image_matches = re.findall(pattern_image, html)
                video_matches = re.findall(pattern_video, html)

                if video_matches:
                    for url in video_matches:
                        logger.debug(url)
                        video_urls.append(url)

                else:
                    if image_matches:
                        for url in image_matches:
                            if 'picasso-static.xiaohongshu.com' not in url:
                                logger.debug(url)
                                image_urls.append(url)

                logger.info(f'end{note_url}')
                utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'), [note_url])
                USED_PAGE_URLS.add(note_url)
                
                break

            except Exception as e:
                logger.error(f'{proxy}获取url失败: {e}')
                continue
        
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'), video_urls)
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'images'), image_urls)
    logger.info(f"获取到 {len(video_urls)} 条视频URL, {len(image_urls)}条图片URL。")

    return video_urls, image_urls


def download_xhs_urls(video_urls, image_urls, save_dir, save_way=0):
    """
    下载视频和图片。
    
    :param video_urls: 视频url列表。
    :param image_urls: 图片url列表。
    :param save_dir: 保存路径。
    :param save_way: 下载方式: save_way=0表示下载视频和图片，=1表示只下载视频，=2表示只下载图片
    """
    image_dir = os.path.join(save_dir, 'image')
    video_dir = os.path.join(save_dir, 'video')
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    if not video_urls and not image_urls:
        logger.warning('urls empty')
        return

    old_video_idx = VIDEO_IDX
    old_image_idx = IMAGE_IDX

    if save_way == 0:
        for video_url in video_urls:
            download_xhs_video(video_url, video_dir)
        for image_url in image_urls:
            download_xhs_image(image_url, image_dir)
    elif save_way == 1:
        for video_url in video_urls:
            download_xhs_video(video_url, video_dir)
    else:
        for image_url in image_urls:
            download_xhs_image(image_url, image_dir)
            
    config.update_idx(WEB_NAME, type_name, 'videos', VIDEO_IDX)
    config.update_idx(WEB_NAME, type_name, 'images', IMAGE_IDX)

    logger.info(f"下载全部完成，本次共下载{VIDEO_IDX-old_video_idx}个视频，{IMAGE_IDX-old_image_idx}个图片（新计数值，VIDEO_IDX={VIDEO_IDX},IMAGE_IDX={IMAGE_IDX})")


def download_xhs_video(video_url, save_dir):
    """
    下载视频。
    
    :param video_url: 视频url。
    :param save_dir: 保存目录。
    """
    if not video_url:
        logger.info('视频链接为空，跳过下载。')
        return

    if video_url in USED_VIDEO_URLS:
        logger.info(f"视频链接 {video_url} 已经处理过，跳过下载。")
        return

    for _ in range(5):
        proxy = utils.get_random_proxy()
        try:
            header = {
                'User-Agent': utils.get_random_user_agent(),
                'Referer': 'https://www.xiaohongshu.com/',  # 设置Referer
            }
                
            response = requests.get(video_url, headers=header, proxies={'https': proxy}, stream=True, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常

            current_time = utils.get_formatted_timestamp()
            filename = f'{type_name[0].upper()}_xhsv{VIDEO_IDX:05d}_{current_time}_RGB.mp4'
            save_path = os.path.join(save_dir, filename)

            # 将视频内容写入文件
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)

            utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'), [video_url])
            USED_VIDEO_URLS.add(video_url)
            add_video_idx()

            logger.info(f"视频已成功下载到 {save_path}")
            break
        except Exception as e:
            logger.error(f"{proxy}_下载失败: {e}")
            continue


def download_xhs_image(image_url, save_dir):
    """
    下载图片。
    
    :param image_url: 图片url列表。
    :param save_dir: 保存路径。
    """
    if not image_url:
        logger.info('图片链接为空，跳过下载。')
        return

    if image_url in USED_IMAGE_URLS:
        logger.info(f"图片链接 {image_url} 已经处理过，跳过下载。")
        return

    for _ in range(5):
        proxy = utils.get_random_proxy()
        
        header = {
                'User-Agent': utils.get_random_user_agent(),
                'Referer': 'https://www.xiaohongshu.com/',  # 设置Referer
            }
        try:
            response = requests.get(image_url, headers=header, proxies={'https': proxy}, stream=True, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常
            image_data = response.content

            current_time = utils.get_formatted_timestamp()
            filename = f'{type_name[0].upper()}_xhsi{IMAGE_IDX:05d}_{current_time}_RGB.jpg'
            save_path = os.path.join(save_dir, filename)

            with open(save_path, 'wb') as file:
                file.write(image_data)

            utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'images'), [image_url])
            USED_IMAGE_URLS.add(image_url)
            add_image_idx()

            logger.info(f"图片已成功下载到 {save_path}")
            break
        except requests.exceptions.RequestException as e:
            logger.error(f"{proxy}_下载失败: {e}")
            continue


def run(keywords, save_dir, max_scroll=10, save_way=0, random_proxy=False, random_user_agent=False, 
        headless=False, use_open_chrome=False, need_load=False, have_pages=False, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param keywords: 关键词列表。
    :param save_dir: 保存路径。
    :param max_scroll: 最大滚动次数。
    :param save_way: 保存方式（0=全部，1=仅视频，2=仅图片）。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的Chrome浏览器。
    :param need_load: 是否需要手动登录页面。
    :param have_pages: 是否已经获取过页面链接。
    :param have_urls: 是否已经获取过视频和图片链接。
    """
    os.makedirs(save_dir, exist_ok=True)
    
    old_video_idx = VIDEO_IDX
    old_image_idx = IMAGE_IDX

    for keyword in keywords:
        logger.info(f'========== 开始处理关键词: {keyword} ==========')
        try:
            if have_pages:
                pages = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'))
            else:
                pages = search_xhs_pages(keyword, max_scroll, save_way, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
                need_load = False  # 下次搜索时不需要加载登录页面
                
            if not pages:
                logger.warning(f"关键词[{keyword}]未获取到有效页面链接，跳过。")
                continue
            
            if have_urls:
                video_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'))
                image_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'images'))
            else:
                video_urls, image_urls = get_xhs_urls(pages)
            
            if not video_urls and not image_urls:
                logger.warning(f"关键词[{keyword}]未提取到有效资源，跳过。")
                continue

            download_xhs_urls(video_urls, image_urls, save_dir, save_way)
        except Exception as e:
            logger.error(f"[关键词: {keyword}] 抓取失败: {e}")
        logger.info(f'========== 完成关键词: {keyword} ==========')
    
    utils.end_logger(WEB_NAME, save_dir, type_name, 
                     video_idx=VIDEO_IDX, image_idx=IMAGE_IDX,
                     new_video_count=VIDEO_IDX-old_video_idx, new_image_count=IMAGE_IDX-old_image_idx)
