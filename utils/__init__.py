# -*- coding: utf-8 -*-
#
# Auto created by: auto_generate_init.py
#
"""
Project Name: web_crawler
File Created: 2025.06.13
Author: ZhangYuetao
File Name: __init__.py
Update: 2025.06.20
"""

# 导入 generic_utils 模块中的函数
from .generic_utils import (
    _get_user_agents,
    get_random_user_agent,
    _get_proxies,
    get_random_proxy,
    get_formatted_timestamp,
    save_list_to_txt,
    read_list_from_txt,
    check_video_type,
    create_option,
)

# 导入 log_utils 模块中的函数
from .log_utils import (
    begin_logger,
    end_logger,
)

# 定义包的公共接口
__all__ = [
    # generic_utils
    '_get_user_agents',
    'get_random_user_agent',
    '_get_proxies',
    'get_random_proxy',
    'get_formatted_timestamp',
    'save_list_to_txt',
    'read_list_from_txt',
    'check_video_type',
    'create_option',

    # log_utils
    'begin_logger',
    'end_logger',

]
