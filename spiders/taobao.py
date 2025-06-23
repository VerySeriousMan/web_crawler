# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.02.08
Author: ZhangYuetao
File Name: taobao.py
Update：2025.06.16
"""

import os
import random
import re
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import utils
import config
from logger import logger

WEB_NAME = 'taobao'

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


def get_taobao_pages(keyword, max_page=10, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    搜索淘宝商品页面链接。
    
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
        driver.get('https://login.taobao.com/member/login.jhtml')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")
    
    all_urls = set()
    
    search_url = f'https://s.taobao.com/search?commend=all&page=1&q={keyword}&search_type=item&tab=all'

    driver.get(search_url)
    time.sleep(5)


    for page in range(1, max_page + 1):
        last_height = driver.execute_script("return document.body.scrollHeight")

        for _ in range(5):
            # 模拟滚动到页面底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # 等待加载更多内容

            # 检查是否到底
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("已滚动到页面底部，停止滚动。")
                break
            last_height = new_height

        # 获取所有商品链接
        item_elements = driver.find_elements(By.XPATH, "//div[@class='content--CUnfXXxv']//div[@id='content_items_wrapper']//div//a")

        page_urls = [item.get_attribute("href") for item in item_elements if item.get_attribute("href")]

        # 对每个链接进行检查和提取shop_id和shop_type
        for url in page_urls:
            url_begin = None
            if url.startswith("https://item.taobao.com"):
                url_begin = "https://item.taobao.com/item.htm?id="
            elif url.startswith("https://detail.tmall.com"):
                url_begin = "https://detail.tmall.com/item.htm?id="

            if url_begin:
                # 使用正则表达式提取id
                match = re.search(r'[?&]id=(\d+)', url)
                if match:
                    shop_id = match.group(1)
                    final_url = url_begin + str(shop_id)
                    all_urls.add(final_url)

        logger.info(f"获取第 {page} 页商品链接：{len(all_urls)}条")

        try:
            # 查找并点击“下一页”按钮
            xpath = '//*[@id="search-content-leftWrap"]/div[2]/div[4]/div/div/button[2]/span'
            next_button = driver.find_element(By.XPATH, xpath)
            next_button.click()
            time.sleep(3)  # 等待页面加载
        except Exception as e:
            logger.error("未能找到“下一页”按钮，停止获取：", e)
            break
        
    all_urls = list(all_urls)
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'), all_urls)
    logger.info(f"获取到 {len(all_urls)} 条 URL。")
    
    return all_urls


def search_images_in_taobao_shops(page_urls, max_scroll=10, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    在淘宝商家页面中搜索图片链接。
    
    :param page_urls: 商家页面链接列表。
    :param max_scroll: 最大滚动次数。
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
        driver.get('https://login.taobao.com/member/login.jhtml')
        
        # 等待用户手动登录
        print("请在浏览器中手动登录，登录完成后按 Enter 键继续...")
        input()
        
        logger.info("登录完成,开始搜索")
    
    all_video_urls = []
    
    for page_url in page_urls:
        if page_url in USED_PAGE_URLS:
            logger.info(f"链接 {page_url} 已经处理过，跳过下载。")
            continue
        
        # 加载商品详情页面
        driver.get(page_url)
        time.sleep(float(round(random.uniform(4, 6), 1)))

        # 定位并点击“全部评价”按钮
        try:
            # 使用你提供的固定 XPath 定位元素
            all_reviews_xpath = "/html/body/div[3]/div/div[2]/div[1]/div[2]/div/div[2]/div/div[2]/div[1]/div/div[4]/div"
            all_reviews_button = driver.find_element(By.XPATH, all_reviews_xpath)
            all_reviews_button.click()
            logger.info("成功点击 '全部评价' 按钮。")
        except Exception as e:
            logger.error("点击 '全部评价' 按钮失败:", e)
            # driver.quit()
            return []

        time.sleep(float(round(random.uniform(4, 6), 1)))

        # 点击有图/视频
        try:
            # 使用你提供的固定 XPath 定位元素
            all_reviews_xpath = "/html/body/div[8]/div[2]/div/div[2]/div[1]/div[1]/span[2]"
            all_reviews_button = driver.find_element(By.XPATH, all_reviews_xpath)
            all_reviews_button.click()
            logger.info("成功点击 '有图/视频' 按钮。")
        except Exception as e:
            logger.error("点击 '有图/视频' 按钮失败:", e)
            # driver.quit()

        # 定位评价区域的滚动容器
        try:
            review_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"{all_reviews_xpath}/following::div[contains(@class, 'comments--vOMSBfi2')]"))
            )
            logger.info("找到评价容器。")
        except Exception as e:
            logger.error("找不到评价容器:", e)
            # driver.quit()
            return []

        # 模拟鼠标点击及键盘 PAGE_DOWN 来滚动评价区域
        actions = ActionChains(driver)
        try:
            # 点击评价容器，确保它获得焦点
            actions.move_to_element(review_container).click().perform()
            time.sleep(1)
        except Exception as e:
            logger.error("点击评价容器失败:", e)

        video_urls = []
        parent_divs = []

        last_scroll_top = None

        # 开始模拟 PAGE_DOWN 键滚动
        for i in range(max_scroll):
            logger.info(f"begin{i}")
            
            actions.send_keys(Keys.PAGE_DOWN).perform()
            time.sleep(float(round(random.uniform(1, 2), 1)))  # 等待页面加载

            # 查找所有包含视频的评论
            try:
                video_previews = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f"{all_reviews_xpath}/following::div[contains(@class, 'comments--vOMSBfi2')]//div[contains(@class, 'playerIcon--Q1UZMOJt')]"))
                )
            except Exception as e:
                logger.error(f"在当前页未能找到视频预览，错误信息：{e}。")
                video_previews = []

            # 通过JavaScript获取评论容器的滚动状态
            current_scroll_top = driver.execute_script("return arguments[0].scrollTop;", review_container)
            if current_scroll_top == last_scroll_top:
                logger.info("评论区域已经滚动到底部, 提前退出")
                break

            last_scroll_top = current_scroll_top

            for preview in video_previews:
                try:
                    # 找到预览图的父级 div 并点击它
                    parent_div = preview.find_element(By.XPATH, "./ancestor::div[contains(@class, 'photo--X8gGDqMU')]")
                    if parent_div not in parent_divs:
                        parent_div.click()
                        logger.info('打开视频弹窗')

                        time.sleep(float(round(random.uniform(1, 2), 1)))  # 等待视频弹窗加载

                        # 获取真正的视频 URL
                        video_element = driver.find_element(By.CSS_SELECTOR, "div.itemVideo--PO8f1t5z video")
                        video_urls.append(video_element.get_attribute("src"))
                        parent_divs.append(parent_div)
                        logger.info("获取到的视频 URL:", video_element.get_attribute("src"))

                        # 关闭视频弹窗,模拟按 ESC 退出
                        actions = ActionChains(driver)
                        actions.send_keys(Keys.ESCAPE).perform()
                        logger.info('关闭视频弹窗')

                        time.sleep(float(round(random.uniform(1, 2), 1)))  # 等待弹窗关闭

                except Exception as e:
                    pass
                    # print("发生错误:", e)
            logger.info(f"stop{i}")

        # input("任务完成，按 Enter 键退出...")
        # driver.quit()
        
        utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'used', 'pages'), [page_url])
        USED_PAGE_URLS.add(page_url)
        
        utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'), video_urls)
        all_video_urls.extend(video_urls)
        logger.info(f"完成 {page_url} ,共获取 {len(video_urls)} 条视频URL")
    
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
        download_taobao_video(video_info, save_dir)
    
    config.update_idx(WEB_NAME, type_name, 'videos', VIDEO_IDX)

    logger.info(f"下载全部完成，本次共下载{VIDEO_IDX - old_idx}个视频（新计数值，VIDEO_IDX={VIDEO_IDX})")


def download_taobao_video(video_url, save_dir):
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
        }
        proxy = utils.get_random_proxy()
        
        try:
            response = requests.get(video_url, headers=header, proxies={'http': proxy}, stream=True, timeout=10)
            response.raise_for_status()  # 如果请求失败，抛出异常

            current_time = utils.get_formatted_timestamp()

            filename = f'{type_name[0].upper()}_tb{VIDEO_IDX:05d}_{current_time}_RGB.mp4'

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
            logger.error(f"{proxy}_下载失败: {e}")
            continue


def run(keywords, save_dir, max_page=10, max_scroll=10, random_proxy=False, random_user_agent=False, 
        headless=False, use_open_chrome=False, need_load=False, have_pages=False, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param keywords: 关键词列表。
    :param save_dir: 保存路径。
    :param max_page: 最大爬取页数。
    :param max_scroll: 最大滚动次数。
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
        logger.infov(f'========== 开始处理关键词: {keyword} ==========')
        try:
            if have_pages:
                pages = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'))
            else:
                pages = get_taobao_pages(keyword, max_page, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
                need_load = False  # 下次搜索时不需要加载登录页面
                
            if not pages:
                logger.warning(f"关键词[{keyword}]未获取到有效页面链接，跳过。")
                continue
            
            if have_urls:
                video_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'))
            else:
                video_urls = search_images_in_taobao_shops(pages, max_scroll, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
            
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
