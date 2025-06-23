# -*- coding: utf-8 -*-
"""
Project Name: web_crawler
File Created: 2025.06.09
Author: ZhangYuetao
File Name: start_crawler.py
Update: 2025.06.18
"""

import time

import config

import spiders
import spiders.xhs
import plugins

# ----------基础参数配置----------
save_path = 'download'
type_name = 'food'
keyword_list = ['西瓜', '荔枝']
need_open_chrome = True
need_test_proxy = False
# ----------------------------

basic_setting = config.load_config(config.BASIC_SETTING_PATH, config.BASIC_SETTING_DEFAULT_CONFIG)
basic_setting["save_path"] = save_path
basic_setting["type_name"] = type_name
config.save_config(config.BASIC_SETTING_PATH, basic_setting)

if need_test_proxy:
    plugins.proxy_test.run()
else:
    if need_open_chrome:
        print('begin opening chrome')
        plugins.open_chrome.run()
        time.sleep(5)
        print('success opening chrome')
    

if __name__ == '__main__' and not need_test_proxy:    
    spiders.xhs.run(keywords=keyword_list, save_dir=save_path, max_scroll=3, save_way=2, 
                    random_proxy=False, random_user_agent=False, headless=False, 
                    use_open_chrome=True, need_load=True, have_pages=False, have_urls=False)
