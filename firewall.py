#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
主程序入口

@author:alex
@date:15-2-13
@time:上午11:44        
@contact:alexliyu2012@gmail.com
  
"""
__author__ = 'alex'
import sys
import os
import ConfigParser
import uuid
from subprocess import Popen, PIPE
from utils.heartbeat import HeartBeatManager
from utils.tools import *

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))


def init(ini_file=None):
    cf = ConfigParser.ConfigParser()

    try:
        if ini_file:
            cf.read(ini_file)
        else:
            cf.read(os.path.join(PROJECT_PATH, "config.ini"))
        redis_host = cf.get("REDIS", "IP")
        redis_port = cf.getint("REDIS", "PORT")
        listener_host = cf.get("LISTENING", "IP")
        listener_port = cf.getint("LISTENING", "PORT")

    except Exception, e:
        print e
        sys.exit(1)


    print_info("REDIS端口 %s:%d" % (redis_host, redis_port))
    print_info("监听心跳包端口 %s:%d" % (listener_host, listener_port))
    print_info("开始运行白名单服务........")
    server = HeartBeatManager(redis_host, redis_port, listener_host, listener_port)
    server.run()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        init(sys.argv[1])
    else:
        init()
