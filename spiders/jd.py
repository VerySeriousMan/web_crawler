# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.02.10
Author: ZhangYuetao
File Name: jd.py
Update: 2025.06.20
"""

import os
import time
import random

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

import utils
import config
from logger import logger

WEB_NAME = 'jingdong'

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


def search_in_jd_shops(page_urls, max_pages=20, random_proxy=False, random_user_agent=False, headless=False, use_open_chrome=False, need_load=False):
    """
    在京东商家页面中搜索图片链接。
    
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
    driver = uc.Chrome(options=options)
    
    if need_load:
        logger.info("需要手动登录页面")
        # 加载登录页面
        driver.get('https://www.jd.com/')
        
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
            video_xpath = "//*[@id='detail']/div[1]/ul/li[5]"
            reviews_button = driver.find_element(By.XPATH, video_xpath)
            reviews_button.click()
            logger.info("成功点击 '商品评价' 按钮。")
        except Exception as e:
            logger.error("点击 '商品评价' 按钮失败:", e)
            # driver.quit()
            return []

        time.sleep(float(round(random.uniform(4, 6), 1)))

        try:
            video_xpath = "//*[@id='comment']/div[2]/div[2]/div[1]/ul/li[3]"
            reviews_button = driver.find_element(By.XPATH, video_xpath)
            reviews_button.click()
            logger.info("成功点击 '视频晒单' 按钮。")
        except Exception as e:
            logger.error("点击 '视频晒单' 按钮失败:", e)
            # driver.quit()
            return []

        time.sleep(float(round(random.uniform(4, 6), 1)))

        # 模拟鼠标点击及键盘 PAGE_DOWN 来滚动评价区域
        actions = ActionChains(driver)

        video_urls = []

        for i in range(max_pages):
            logger.info(f"begin第{i}页评论")

            # 开始模拟 PAGE_DOWN 键滚动
            for _ in range(3):
                actions.send_keys(Keys.PAGE_DOWN).perform()
                time.sleep(1.5)  # 等待页面加载

            have_video = 0

            # 获取评论视频url
            try:
                video_wrappers = driver.find_elements(By.CSS_SELECTOR, "div.J-video-view-wrap.clearfix")
                logger.info(f"第{i}页找到 {len(video_wrappers)} 个视频包装器")
                for wrapper in video_wrappers:
                    try:
                        # 从包装器中查找 <video> 元素，并获取其 src 属性
                        video_element = wrapper.find_element(By.TAG_NAME, "video")
                        video_url = video_element.get_attribute("src")
                        if video_url and video_url not in video_urls:
                            video_urls.append(video_url)
                            have_video = 1
                            logger.info("获取到的视频 URL:", video_url)
                    except Exception as e:
                        logger.error("获取视频 URL 失败:", e)
            except Exception as e:
                logger.error("查找视频包装器失败:", e)

            if have_video == 0:
                logger.info("当前页面已无视频。提前退出")
                break

            try:
                # 定位到当前显示的评论容器，这里以视频晒单为（#comment-2）
                video_container = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "#comment-2"))
                )

                # 在当前容器内查找所有“下一页”按钮
                next_page_buttons = video_container.find_elements(By.CSS_SELECTOR, "a.ui-pager-next[href='#comment']")

                # 筛选出可见的按钮
                next_page_button = None
                for btn in next_page_buttons:
                    if btn.is_displayed():
                        next_page_button = btn
                        break

                if not next_page_button:
                    raise Exception("未找到可见的下一页按钮。")

                # 使用 JavaScript 点击按钮
                driver.execute_script("arguments[0].click();", next_page_button)
                logger.info("成功点击 '下一页' 按钮。")
                time.sleep(float(round(random.uniform(2.5, 3.5), 1)))

            except Exception as e:
                logger.error("点击 '下一页' 按钮失败:", e)
                break

            logger.info(f"stop第{i}页评论")

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
        download_jd_video(video_info, save_dir)

    config.update_idx(WEB_NAME, type_name, 'videos', VIDEO_IDX)

    logger.info(f"下载全部完成，本次共下载{VIDEO_IDX - old_idx}个视频（新计数值，VIDEO_IDX={VIDEO_IDX})")


def download_jd_video(video_url, save_dir):
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

            filename = f'{type_name[0].upper()}_jd{VIDEO_IDX:05d}_{current_time}_RGB.mp4'

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
        pages = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'pages'))
            
        if not pages:
            logger.warning(f"[{type_name}]未获取到有效页面链接，提前退出。")
            return
        
        if have_urls:
            video_urls = utils.read_list_from_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'))
        else:
            video_urls = search_in_jd_shops(pages, max_page, random_proxy, random_user_agent, headless, use_open_chrome, need_load)
        
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
        