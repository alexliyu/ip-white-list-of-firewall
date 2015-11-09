# -*- coding:utf-8 -*-
"""
主数据模型管理

@author:alex
@date:15-3-14
@time:上午3:06        
@contact:alexliyu2012@gmail.com
  
"""
__author__ = 'alex'

from datetime import datetime, date, timedelta
import logging
import logging.handlers

logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)

current_date = date.today()

# 创建一个handler，用于写入日志文件
fh = logging.handlers.TimedRotatingFileHandler('log/firewall', "midnight", 1, 0)
fh.setLevel(logging.INFO)
fh.suffix = "%Y-%m-%d.log"
# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# 定义handler的输出格式
formatter = logging.Formatter('[%(process)d] %(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 给logger添加handler
logger.addHandler(fh)
logger.addHandler(ch)


def print_log(info, msg):
    """
    打印输出
    :param msg:
    :return:
    """
    print "[%s][%s] %s" % (info, str(datetime.now()), msg)


def print_debug(msg):
    logger.debug(msg)


def print_info(msg):
    """
    打印输出
    :param msg:
    :return:
    """
    logger.info(msg)


def print_warn(msg):
    """
    打印输出
    :param msg:
    :return:
    """
    logger.warning(msg)


def print_error(msg):
    """
    打印输出
    :param msg:
    :return:
    """
    logger.error(msg)