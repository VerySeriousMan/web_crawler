# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.04.01
Author: ZhangYuetao
File Name: baidutieba.py
Update: 2025.06.20
"""

import os
import random
import time

import requests
import zyt_validation_utils
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from pypinyin import lazy_pinyin

import utils
import config
from logger import logger

WEB_NAME = 'baidutieba'

basic_setting = config.load_config(config.BASIC_SETTING_PATH, config.BASIC_SETTING_DEFAULT_CONFIG)
save_path = basic_setting["save_path"]
type_name = basic_setting["type_name"]

IMAGE_IDX = config.get_idx(WEB_NAME, type_name, 'images')
PAGE_IDX = config.get_idx(WEB_NAME, type_name, 'pages')

USED_IMAGE_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'images'))
USED_PAGE_URLS = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'))

utils.begin_logger(WEB_NAME, save_path, type_name, 
                   image_idx=IMAGE_IDX, page_idx=PAGE_IDX, 
                   used_image_urls=USED_IMAGE_URLS, used_page_urls=USED_PAGE_URLS)


def add_image_idx():
    """
    增加图片索引。
    """
    global IMAGE_IDX
    IMAGE_IDX = IMAGE_IDX + 1


def add_page_idx():
    """
    增加帖子索引。
    """
    global PAGE_IDX
    PAGE_IDX = PAGE_IDX + 1


def get_pages(max_page=10, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    搜索百度贴吧页面链接。
    
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
        driver.get('https://tieba.baidu.com')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")
        
    page_urls = set()

    for i in range(max_page):
        search_url = f"https://tieba.baidu.com/f?kw={type_name}&ie=utf-8&pn={i * 50}"

        driver.get(search_url)
        time.sleep(3)

        post_links = driver.find_elements(By.CSS_SELECTOR, "a.j_th_tit")
        for link in post_links:
            page = link.get_attribute("href")
            page_urls.add(page)

        logger.info(f"第{i + 1}页找到{len(post_links)}个帖子")

    page_urls = list(page_urls)
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'), page_urls)
    logger.info(f"爬取帖子完成，共{len(page_urls)}个帖子")

    return page_urls


def get_image_urls(page_urls):
    """
    获取图片链接。
    
    :param page_urls: 页面URL列表。
    :return: 图片url列表。
    """
    image_urls = set()
    
    load_cookies = config.load_config(config.LOAD_COOKIES_PATH, config.LOAD_COOKIES_DEFAULT_CONFIG)
    badutieba_cookie = load_cookies["badutieba_cookie"]

    for url in page_urls:
        if url in USED_PAGE_URLS:
            logger.info(f"页面链接 {url} 已经处理过，跳过下载。")
            continue
        
        time.sleep(round(random.uniform(1, 1.5), 2))

        ts_image_urls = set()

        retries = 0
        max_retries = 3
        response = None
        while retries < max_retries:
            try:
                headers = {
                    'User-Agent': utils.get_random_user_agent(),
                    "Referer": 'https://tieba.baidu.com/',
                    'cookie': badutieba_cookie,
                }

                response = requests.get(url, headers=headers, proxies={'https': utils.get_random_proxy()}, timeout=10)

                response.raise_for_status()

                break
            except Exception as e:
                logger.error(f'{e}, begin retry')
                retries += 1  # 失败后增加重试次数

        if not response:
            continue

        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取所有 <img> 标签
        image_tags = soup.find_all('img', class_="BDE_Image")  # 根据 class 过滤

        for img in image_tags:
            src = img.get('src')
            if src:  # 确保 src 不为空
                ts_image_urls.add((PAGE_IDX, src))

        if not zyt_validation_utils.is_empty(ts_image_urls):
            image_urls.update(ts_image_urls)
            add_page_idx()

            logger.info(f'完成{url}，获取{len(ts_image_urls)}个图片')
        else:
            logger.warning(f'完成{url}，内容为空')

        utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'), [url])
        USED_PAGE_URLS.add(url)
    
    image_urls = list(image_urls)

    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'images'), image_urls)
    config.update_idx(WEB_NAME, type_name, 'pages', PAGE_IDX)
    logger.info(f'共获取{len(image_urls)}个图片')

    return image_urls


def download_image(image_info, save_dir):
    """
    下载单个图片。
    
    :param image_info: 图片信息。
    :param save_dir: 保存目录。
    """
    if not image_info:
        logger.info('图片链接为空，跳过下载。')
        return

    image_id = image_info[0]
    image_url = image_info[1]

    if image_url in USED_IMAGE_URLS:
        logger.info(f"图片链接 {image_url} 已经处理过，跳过下载。")
        return

    if image_url.endswith('.gif'):
        return
    
    for _ in range(5):
        header = {
            'User-Agent': utils.get_random_user_agent(),
        }
        proxy = {'https': utils.get_random_proxy()}
        try:
            response = requests.get(image_url, headers=header, proxies=proxy, stream=True, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常
            
            image_data = response.content

            current_time = utils.get_formatted_timestamp()
            pinyin_list = lazy_pinyin(type_name)
            pinyin_title = ''
            for pinyin in pinyin_list:
                pinyin_title += pinyin[0].lower()
            
            filename = f'{type_name[0].upper()}_bdtb{pinyin_title}{image_id:05d}_{current_time}_RGB.jpg'
            dir_name = f'bdtb{pinyin_title}{image_id:05d}'
            save_path = os.path.join(save_dir, dir_name, filename)
            os.makedirs(os.path.join(save_dir, dir_name), exist_ok=True)

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


def download_images(image_infos, save_dir):
    """
    下载图片。
    
    :param image_infos: 图片信息列表。
    :param save_dir: 保存目录。
    """
    if not image_infos:
        logger.warning('urls empty')
        return

    os.makedirs(save_dir, exist_ok=True)
    old_image_idx = IMAGE_IDX

    for image_info in image_infos:
        download_image(image_info, save_dir)
        time.sleep(round(random.uniform(0.1, 0.3), 2))
    
    config.update_idx(WEB_NAME, type_name, 'images', IMAGE_IDX)

    logger.info(f"下载全部完成，本次共下载{IMAGE_IDX - old_image_idx}个图片（新计数值:IMAGE_IDX={IMAGE_IDX})")


def run(save_dir, max_page=10, random_proxy=False, random_user_agent=False, headless=False, 
        use_open_chrome=False, need_load=False, have_pages=False, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param save_dir: 保存路径。
    :param max_page: 最大爬取页面数量。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的Chrome浏览器。
    :param need_load: 是否需要手动登录页面。
    :param have_pages: 是否已经获取过页面链接。
    :param have_urls: 是否已经获取过图片链接。
    """
    os.makedirs(save_dir, exist_ok=True)
    
    old_image_idx = IMAGE_IDX
    old_page_idx = PAGE_IDX

    logger.info(f'========== 开始处理: {type_name} ==========')
    try:
        if have_pages:
            pages = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'))
        else:
            pages = get_pages(max_page, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
            
        if not pages:
            logger.warning(f"[{type_name}]未获取到有效页面链接，提前退出。")
            return
        
        if have_urls:
            image_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'images'))
        else:
            image_urls = get_image_urls(pages)
        
        if not image_urls:
            logger.warning(f"[{type_name}]未提取到有效资源，提前退出。")
            return
        
        download_images(image_urls, save_dir)
    except Exception as e:
        logger.error(f"[{type_name}] 抓取失败: {e}")
    logger.info(f'========== 完成: {type_name} ==========')
    
    utils.end_logger(WEB_NAME, save_dir, type_name, 
                     image_idx=IMAGE_IDX, page_idx=PAGE_IDX,
                     new_image_count=IMAGE_IDX-old_image_idx, new_page_count=PAGE_IDX-old_page_idx)
        