# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.02.18
Author: ZhangYuetao
File Name: amazon.py
Update: 2025.06.20
"""

import os
import time
import random

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

import utils
import config
from logger import logger

WEB_NAME = 'amazon'

basic_setting = config.load_config(config.BASIC_SETTING_PATH, config.BASIC_SETTING_DEFAULT_CONFIG)
save_path = basic_setting["save_path"]
type_name = basic_setting["type_name"]

VIDEO_IDX = config.get_idx(WEB_NAME, type_name, 'videos')

USED_VIDEO_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'))
USED_PAGE_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'goods'))

utils.begin_logger(WEB_NAME, save_path, type_name, 
                   video_idx=VIDEO_IDX,
                   used_video_urls=USED_VIDEO_URLS, used_page_urls=USED_PAGE_URLS)


def add_idx():
    """
    增加视频索引。
    """
    global VIDEO_IDX
    VIDEO_IDX = VIDEO_IDX + 1


def search_in_amazon_shops(amazon_goods, max_pages=20, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    在亚马逊商家页面中搜索图片链接。
    
    :param amazon_goods: 亚马逊商品列表。
    :param max_pages: 最大搜索页数。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机 User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的 Chrome 浏览器。
    :param need_load: 是否需要手动登录页面。
    :return: 图片链接列表。
    """
    options = utils.create_option(random_proxy, random_user_agent, headless, use_open_chrome)
    driver = webdriver.Chrome(options=options)
    
    if need_load:
        logger.info("需要手动登录页面")
        # 加载登录页面
        driver.get('https://www.amazon.com/')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")
    
    all_video_urls = []
    
    for amazon_good in amazon_goods:
        if amazon_good in USED_PAGE_URLS:
            logger.info(f"物品 {amazon_good} 已经处理过，跳过下载。")
            continue
            
        video_urls = []

        for page in range(max_pages):
            # 加载商品详情页面
            shop_url = f"{amazon_good}/ref=cm_cr_arp_d_paging_btm_next_3" \
                    f"?ie=UTF8&reviewerType=all_reviews&mediaType=media_reviews_only&pageNumber={page+1} "
            driver.get(shop_url)
            time.sleep(float(round(random.uniform(4, 6), 1)))

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            no_reviews_message = soup.find('span', class_='a-size-medium',
                                        text='Sorry, no reviews match your current selections.')
            if no_reviews_message:
                logger.warning(f"No more reviews found. Exiting early.")
                break

            # 查找所有 video 标签并提取 src 属性
            video_input_tags = soup.find_all('input', class_='video-url')

            for video_input in video_input_tags:
                video_url = video_input.get('value')
                if video_url and video_url.endswith('.mp4'):
                    video_urls.append(video_url)
                    
        utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'goods'), [amazon_good])
        USED_PAGE_URLS.add(amazon_good)
        
        utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'), video_urls)
        all_video_urls.extend(video_urls)
        logger.info(f"完成 {amazon_good} ,共获取 {len(video_urls)} 条视频URL")
    
    logger.info(f"完成全部视频链接获取 ,共获取 {len(all_video_urls)} 条视频URL")
        
    return all_video_urls


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
        download_amazon_video(video_info, save_dir)
    
    config.update_idx(WEB_NAME, type_name, 'videos', VIDEO_IDX)

    logger.info(f"下载全部完成，本次共下载{VIDEO_IDX - old_idx}个视频（新计数值，VIDEO_IDX={VIDEO_IDX})")


def download_amazon_video(video_url, save_dir):
    """
    下载单个视频。

    :param video_url: 视频url。
    :param save_dir: 保存路径。
    """ 
    if not video_url:
        logger.info('视频链接为空，跳过下载。')
        return

    if video_url in USED_VIDEO_URLS:
        logger.info(f"视频链接 {video_url} 已经处理过，跳过下载。")
        return

    for i in range(3):
        header = {
            'User-Agent': utils.get_random_user_agent(),
        }
        proxies = {
            'http': 'http://127.0.0.1:2081',
            'https': 'http://127.0.0.1:2081',
        }
        
        try:
            response = requests.get(video_url, headers=header, proxies=proxies, stream=True, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常

            current_time = utils.get_formatted_timestamp()

            filename = f'{type_name[0].upper()}_amazon{VIDEO_IDX:05d}_{current_time}_RGB.mp4'

            save_path = os.path.join(save_dir, filename)

            # 将视频内容写入文件
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)

            # 判断视频类型
            try:
                video_type = utils.check_video_type(save_path)  # 调用前面定义的函数
            except:
                video_type = "RGB"

            # 如果是 IR 视频，修改文件名
            if video_type == "IR":
                new_filename = filename.replace("_RGB.mp4", "_IR.mp4")
                new_save_path = os.path.join(save_dir, new_filename)
                os.rename(save_path, new_save_path)
                save_path = new_save_path  # 更新路径

            utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'videos'), [video_url])
            USED_VIDEO_URLS.add(video_url)
            add_idx()

            logger.info(f"视频已成功下载到 {save_path}")
            break
        except requests.exceptions.RequestException as e:
            logger.warning(f"第{i}次下载失败: {e}")
            continue


def run(save_dir, max_page=10, random_proxy=False, random_user_agent=False, 
        headless=False, use_open_chrome=False, need_load=False, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param save_dir: 保存路径。
    :param max_page: 最大爬取页数。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的Chrome浏览器。
    :param need_load: 是否需要手动登录页面。
    :param have_urls: 是否已经获取过视频链接。
    """
    os.makedirs(save_dir, exist_ok=True)
    
    old_video_idx = VIDEO_IDX

    logger.info(f'========== 开始处理: {type_name} ==========')
    try:
        amazon_goods = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'goods'))
            
        if not amazon_goods:
            logger.warning(f"[{type_name}]未获取到有效页面链接，提前退出。")
            return
        
        if have_urls:
            video_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'))
        else:
            video_urls = search_in_amazon_shops(amazon_goods, max_page, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
        
        if not video_urls:
            logger.warning(f"[{type_name}]未提取到有效资源，提前退出。")
            return

        download_videos(video_urls, save_dir)
    except Exception as e:
        logger.error(f"[{type_name}] 抓取失败: {e}")
    logger.info(f'========== 完成: {type_name} ==========')
    
    utils.end_logger(WEB_NAME, save_dir, type_name, 
                     video_idx=VIDEO_IDX,
                     new_video_count=VIDEO_IDX-old_video_idx)
    