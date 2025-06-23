# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2024.12.04
Author: ZhangYuetao
File Name: youtube.py
Update: 2025.06.20
"""

import os

import socks
import socket
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build

import config
import utils
from logger import logger

socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 2080)  # 代理地址和端口
socket.socket = socks.socksocket

WEB_NAME = 'youtube'

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


def search_youtube_videos(keyword, max_results=10):
    """
    根据关键词搜索YouTube视频，返回前max_results个视频的URL。
    
    :param keyword: 搜索关键词。
    :param max_results: 最大搜索结果数。
    :return: 搜索结果的视频URL列表。
    """
    api_key = config.GOOGLE_API_KEY  # google_api_key

    youtube = build('youtube', 'v3', developerKey=api_key)

    search_response = youtube.search().list(
        q=keyword,
        type='video',
        part='id,snippet',
        maxResults=max_results
    ).execute()

    video_urls = [f'https://www.youtube.com/watch?v={item["id"]["videoId"]}' for item in search_response['items']]
    utils.save_list_to_txt(config.get_save_history_path(WEB_NAME, type_name, 'get', 'videos'), video_urls)
    logger.info(f"爬取页面完成，共{len(video_urls)}个URL")
    
    return video_urls


def download_video(video_url, save_path, proxy='http://127.0.0.1:2081', retries=3):
    """
    下载单个视频函数。
    
    :param video_url: 视频的URL。
    :param save_path: 保存路径。
    :param proxy: 代理设置。
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
    filename = f'{type_name[0].upper()}_ytb{VIDEO_IDX:05d}_{current_time}_RGB.mp4'

    # 配置 yt_dlp 的参数
    ydl_opts = {
        'proxy': proxy,  # 设置代理
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
            logger.error(f"尝试 {attempt + 1}/{retries} 失败: {e}")
    else:
        logger.error(f"所有尝试均失败，无法下载视频 {video_url}。")


def download_videos(video_urls, save_path, proxy=None, retries=3):
    """
    根据关键词搜索并下载前 num_videos 个视频。
    
    :param video_urls: 视频URL列表。
    :param save_path: 保存路径。
    :param proxy: 代理设置。
    :param retries: 重试次数。
    """
    os.makedirs(save_path, exist_ok=True)

    if not video_urls:
        logger.warning("未找到相关视频。")
    
    old_video_idx = VIDEO_IDX

    logger.info(f"导入 {len(video_urls)} 个视频，开始下载...")

    for url in video_urls:
        logger.info(f"正在下载视频 {url}")
        download_video(url, save_path, proxy, retries)

    config.update_idx(WEB_NAME, type_name, 'videos', VIDEO_IDX)

    logger.info(f"下载全部完成，本次共下载{VIDEO_IDX-old_video_idx}个视频（新计数值，VIDEO_IDX={VIDEO_IDX})")


def run(keywords, save_dir, max_results=10, proxy=None, retries=3, have_urls=False):
    """
    统一入口函数，供调度器调用。
    
    :param keywords: 关键词列表。
    :param save_dir: 保存路径。
    :param max_results: 最大抓取视频数量。
    :param proxy: 代理设置。
    :param retries: 重试次数。
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
                video_urls = search_youtube_videos(keyword, max_results)
            
            if not video_urls:
                logger.warning(f"关键词[{keyword}]未提取到有效资源，跳过。")
                continue

            download_videos(video_urls, save_dir, proxy, retries)
        except Exception as e:
            logger.error(f"[关键词: {keyword}] 抓取失败: {e}")
        logger.info(f'========== 完成关键词: {keyword} ==========')
    
    utils.end_logger(WEB_NAME, save_dir, type_name, 
                     video_idx=VIDEO_IDX,
                     new_video_count=VIDEO_IDX-old_video_idx)
