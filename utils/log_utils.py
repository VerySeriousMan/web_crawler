# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.06.20
Author: ZhangYuetao
File Name: log_utils.py
Update: 2025.06.20
"""

import time
from logger import logger

crawl_context = {}


def begin_logger(WEB_NAME, save_path, type_name, video_idx=None, image_idx=None, page_idx=None, used_video_urls=[], used_image_urls=[], used_page_urls=[]):
    """
    开始日志记录。

    :param WEB_NAME: 爬取的网站名称。
    :param save_path: 保存路径。
    :param type_name: 爬取的类型名称。
    :param video_idx: 视频索引。
    :param image_idx: 图片索引。
    :param page_idx: 页面索引。
    :param used_video_urls: 已爬取的视频 URL 列表。
    :param used_image_urls: 已爬取的图片 URL 列表。
    :param used_page_urls: 已爬取的页面 URL 列表。
    """
    crawl_context.clear()
    crawl_context["start_time"] = time.time()

    logger.info(f"--------------------开始爬虫--------------------")
    logger.info(f"当前爬取网站：{WEB_NAME}")
    logger.info(f"当前爬取类型：{type_name}")
    logger.info(f"当前保存路径：{save_path}")
    logger.info(f"------------------已用历史数据------------------")
    logger.info(f"历史已爬取视频数量：{len(used_video_urls)}，当前视频索引：{video_idx}")
    logger.info(f"历史已爬取图片数量：{len(used_image_urls)}，当前图片索引：{image_idx}")
    logger.info(f"历史已爬取页面数量：{len(used_page_urls)}，当前页面索引：{page_idx}")
    logger.info(f"------------------------------------------------")


def end_logger(WEB_NAME, save_path, type_name, video_idx=None, image_idx=None, page_idx=None, new_video_count=0, new_image_count=0, new_page_count=0):
    """
    结束日志记录。

    :param save_path: 保存路径。
    :param type_name: 爬取的类型名称。
    :param video_idx: 视频索引。
    :param image_idx: 图片索引。
    :param page_idx: 页面索引。
    :param new_video_count: 新增视频数量。
    :param new_image_count: 新增图片数量。
    :param new_page_count: 新增页面数量。
    """
    elapsed_time = time.time() - crawl_context.get("start_time", time.time())

    logger.info(f"--------------------爬虫结束--------------------")
    logger.info(f"当前爬取网站：{WEB_NAME}")
    logger.info(f"当前爬取类型：{type_name}")
    logger.info(f"当前保存路径：{save_path}")
    logger.info(f"------------------运行统计信息------------------")
    logger.info(f"本次新增视频数量：{new_video_count}，当前视频索引：{video_idx}")
    logger.info(f"本次新增图片数量：{new_image_count}，当前图片索引：{image_idx}")
    logger.info(f"本次新增页面数量：{new_page_count}，当前页面索引：{page_idx}")
    logger.info(f"总耗时：{elapsed_time:.2f} 秒")
    logger.info(f"------------------------------------------------")
