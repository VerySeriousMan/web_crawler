# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.05.16
Author: ZhangYuetao
File Name: pet_finder.py
Update: 2025.06.20
"""

import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import utils
import config
from logger import logger

IMAGE_IDX_LOCK = threading.Lock()        # 用于保护 IMAGE_IDX 的修改
USED_URLS_LOCK = threading.Lock()        # 用于保护 USED_IMAGE_URLS 的访问
FILE_LOCKS = {                           # 用于保护写文件的操作
    'success': threading.Lock(),
    'fail': threading.Lock(),
}

WEB_NAME = 'petfinder'

basic_setting = config.load_config(config.BASIC_SETTING_PATH, config.BASIC_SETTING_DEFAULT_CONFIG)
save_path = basic_setting["save_path"]
type_name = basic_setting["type_name"]

IMAGE_IDX = config.get_idx(WEB_NAME, type_name, 'images')

used_images = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'images'))
wrong_images = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'wrong', 'images'))
USED_IMAGE_URLS = used_images.update(wrong_images)
used_pages = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'))
wrong_pages = config.init_used_urls(config.get_save_history_path(WEB_NAME, type_name, 'wrong', 'pages'))
USED_PAGE_URLS = used_pages.update(wrong_pages)

utils.begin_logger(WEB_NAME, save_path, type_name, 
                   image_idx=IMAGE_IDX, 
                   used_image_urls=USED_IMAGE_URLS, used_page_urls=USED_PAGE_URLS)


def add_idx():
    """
    增加图片索引。
    """
    global IMAGE_IDX
    with IMAGE_IDX_LOCK:
        IMAGE_IDX += 1


def search_pet_pages(max_pages=10, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    搜索 PetFinder 页面链接。
    
    :param max_pages: 最大搜索页数。
    :param random_proxy: 是否使用随机代理。
    :param random_user_agent: 是否使用随机 User-Agent。
    :param headless: 是否启用无头模式。
    :param use_open_chrome: 是否使用已打开的 Chrome 浏览器。
    :param need_load: 是否需要手动登录页面。
    :return: 搜索到的页面链接列表。
    """
    options = utils.create_option(random_proxy, random_user_agent, headless, use_open_chrome)
    
    driver = webdriver.Chrome(options=options)

    all_urls = set()
    
    if need_load:
        logger.info("需要手动登录页面")
        # 加载登录页面
        driver.get('https://www.petfinder.com/search/cats-for-adoption/us/ca/los-angeles/?distance=Anywhere')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")

    for page in range(max_pages):
        logger.info(f"begin page: [{page}]")
        # 加载搜索页面
        time.sleep(5)
        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                page_links = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.petCard-link')))

                logger.info(f"get {len(page_links)} urls")
                for page_link in page_links:
                    page_url = page_link.get_attribute('href')

                    if page_url and 'www.petfinder.com/cat' in page_url:
                        all_urls.add(page_url)

                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        'button.fieldBtn.fieldBtn_altHover.m-fieldBtn_iconRt.m-fieldBtn_tight.m-fieldBtn_full')))

                next_button.click()
                break
            except Exception as e:
                retries += 1  # 失败后增加重试次数
                if retries == max_retries:
                    logger.error(f"重试次数达到最大值，查找失败:{e}。")
                    
                logger.error(f"失败，进行重试，重试次数：{retries}/{max_retries}，错误信息：{e}")
                driver.refresh()
                time.sleep(10)
                
        if retries == max_retries:
            logger.error(f"提早退出：{page}")
            break

    all_urls = list(all_urls)
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'), all_urls)
    logger.info(f"获取到 {len(all_urls)} 条 URL。")

    return all_urls


def fetch_images_from_page(page_url):
    """
    从单个页面获取图片链接。
    
    :param page_url: 页面 URL。
    :return: 图片链接列表或失败的 URL。
    """
    if page_url in USED_PAGE_URLS:
        logger.info(f"链接 {page_url} 已经处理过，跳过下载。")
        return [], None
        
    proxies = {
        'http': 'http://127.0.0.1:2081',
        'https': 'http://127.0.0.1:2081',
    }
    pet_id = page_url.split('/')[4].split('-')[-1]

    for i in range(3):
        header = {
            'User-Agent': utils.get_random_user_agent(),
        }

        try:
            response = requests.get(page_url, headers=header, proxies=proxies, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            image_tags = soup.find_all('img', class_='petCarousel-body-slide')

            urls = [(pet_id, img.get('src')) for img in image_tags if img.get('src')]
            USED_PAGE_URLS.add(page_url)
            logger.info(f"✅ 成功获取图片 from {page_url} — 共 {len(urls)} 张")
            
            return urls, None
        
        except Exception as e:
            logger.error(f"❌ 获取失败 ({page_url}), 重试第 {i + 1} 次: {e}")

    return [], page_url  # 返回空图像和失败的 URL


def get_images_in_pages(page_urls, max_workers=5):
    """
    从页面列表中获取全部图像链接。
    
    :param page_urls: 页面 URL 列表。
    :param max_workers: 最大工作线程数。
    :return: 图像链接列表。
    """
    all_urls = []
    wrong_urls = []
    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_images_from_page, url): url for url in page_urls}

        for i, future in enumerate(as_completed(future_to_url), 1):
            urls, wrong_url = future.result()

            with lock:
                all_urls.extend(urls)  # 将图像 URL 添加到列表
                if wrong_url:
                    wrong_urls.append(wrong_url)  # 将失败的 URL 添加到列表

                if i % 100 == 0:
                    logger.info(f"⚙️ 已处理 {i} 个页面，保存中...")
                    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'images'), all_urls)
                    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'wrong', 'pages'), wrong_urls)
                    all_urls.clear()
                    wrong_urls.clear()

    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'images'), all_urls)
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'wrong', 'pages'), wrong_urls)
    logger.info(f"🎉 全部完成，共处理 {len(page_urls)} 个页面。")

    return all_urls


def download_images_thread(image_infos, save_dir, max_workers=8):
    """
    多线程下载图像。
    
    :param image_infos: 图像信息列表。
    :param save_dir: 保存目录。
    :param max_workers: 最大工作线程数。
    """
    os.makedirs(save_dir, exist_ok=True)
    if not image_infos:
        logger.warning('urls empty')
        return

    old_idx = IMAGE_IDX

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_image, info, save_dir) for info in image_infos]
        for future in as_completed(futures):
            future.result()
            
    config.update_idx(WEB_NAME, type_name, 'images', IMAGE_IDX)
    
    logger.info(f"下载全部完成，本次共下载{IMAGE_IDX - old_idx}个视频（新计数值，IMAGE_IDX={IMAGE_IDX})")


def download_images(image_infos, save_dir):
    """
    单线程下载图像。
    
    :param image_infos: 图像信息列表。
    :param save_dir: 保存目录。
    """
    os.makedirs(save_dir, exist_ok=True)
    if not image_infos:
        logger.warning('urls empty')
        return

    old_idx = IMAGE_IDX

    for image_info in image_infos:
        download_image(image_info, save_dir)
    
    config.update_idx(WEB_NAME, type_name, 'images', IMAGE_IDX)

    logger.info(f"下载全部完成，本次共下载{IMAGE_IDX - old_idx}个视频（新计数值，IMAGE_IDX={IMAGE_IDX})")


def download_image(image_info, save_dir):
    """
    下载图像。
    
    :param image_info: 图像信息。
    :param save_dir: 保存目录。
    """
    if not image_info:
        logger.info('empty！')
        return

    image_id = image_info[0]
    image_url = image_info[1]

    with USED_URLS_LOCK:
        if image_url in USED_IMAGE_URLS:
            logger.info(f"图片链接 {image_url} 已经处理过，跳过下载。")
            return

    # 发送 GET 请求获取视频内容
    header = {
        'User-Agent': utils.get_random_user_agent(),
    }

    wrong_url = None

    for _ in range(3):
        proxies = {
            'http': 'http://127.0.0.1:2081',
            'https': 'http://127.0.0.1:2081',
        }
        try:
            response = requests.get(image_url, headers=header, proxies=proxies, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常
            image_data = response.content

            current_time = utils.get_formatted_timestamp()

            filename = f'{type_name[0].upper()}_pf{image_id}_{current_time}_RGB.jpg'
            dir_name = f'pf{image_id}'

            save_path = os.path.join(save_dir, dir_name, filename)
            os.makedirs(os.path.join(save_dir, dir_name), exist_ok=True)

            with open(save_path, 'wb') as file:
                file.write(image_data)

            with FILE_LOCKS['success']:
                utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'images'), [image_url])

            with USED_URLS_LOCK:
                USED_IMAGE_URLS.add(image_url)

            add_idx()

            logger.info(f"图片已成功下载到 {save_path}")
            wrong_url = None
            break
        except requests.exceptions.RequestException as e:
            logger.error(f"下载失败: {e}")
            wrong_url = image_url
            continue

    if wrong_url:
        with FILE_LOCKS['fail']:
            utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'wrong', 'images'), [wrong_url])


def run(save_dir, max_page=10, max_search_workers=1, max_download_workers=1, random_proxy=False, random_user_agent=False, 
        headless=False, use_open_chrome=False, need_load=True, have_pages=False, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param save_dir: 保存路径。
    :param max_page: 最大爬取页面数量。
    :param max_search_workers: 最大搜索线程数。
    :param max_download_workers: 最大下载线程数。
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

    logger.info(f'========== 开始处理: {type_name} ==========')
    try:
        if have_pages:
            pages = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'))
        else:
            pages = search_pet_pages(max_page, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
            
        if not pages:
            logger.warning(f"[{type_name}]未获取到有效页面链接，提前退出。")
            return
        
        if have_urls:
            image_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'images'))
        else:
            image_urls = get_images_in_pages(pages, max_search_workers)
        
        if not image_urls:
            logger.warning(f"[{type_name}]未提取到有效资源，提前退出。")
            return
        
        if max_download_workers == 1:
            download_images(image_urls, save_dir)
        else:
            download_images_thread(image_urls, save_dir, max_download_workers)
    except Exception as e:
        logger.error(f"[{type_name}] 抓取失败: {e}")
    logger.info(f'========== 完成: {type_name} ==========')
    
    utils.end_logger(WEB_NAME, save_dir, type_name, 
                     image_idx=IMAGE_IDX,
                     new_image_count=IMAGE_IDX-old_image_idx)
        