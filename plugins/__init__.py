# -*- coding: utf-8 -*-
#
# Auto created by: auto_generate_init.py
#
"""
Project Name: web_crawler
File Created: 2025.06.18
Author: ZhangYuetao
File Name: __init__.py
Update: 2025.06.18
"""

# 导入 open_chrome 模块中的函数
from .open_chrome import (
    run,
)

# 导入 proxy_test 模块中的函数
from .proxy_test import (
    load_proxies,
    validate_proxy,
    save_results,
    run,
)

# 定义包的公共接口
__all__ = [
    # open_chrome
    'run',

    # proxy_test
    'load_proxies',
    'validate_proxy',
    'save_results',
    'run',

]
