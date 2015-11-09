# -*- coding:utf-8 -*-
"""
主数据模型管理

@author:alex
@date:15-2-26
@time:下午5:24        
@contact:alexliyu2012@gmail.com
  
"""
__author__ = 'alex'
import os
import re
import time
import sys
import signal
import _socket
import gevent
import redis
import binascii
from gevent import socket
from gevent.queue import Queue
from pyroute2 import ipset
from Crypto.Cipher import ARC4
from utils.tools import *
from gevent.server import DatagramServer
from gevent.lock import Semaphore
from gevent import monkey;monkey.patch_os()
import multiprocessing
from multiprocessing import Process, Queue as PQueue

SEED_KEY = 'cloudtv.bz'
TIMEOUT = 60*60*2
IPSET_NAME = 'white_list'
ipv4_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')


class UdpServer(DatagramServer):

    def __init__(self, *args, **kwargs):
        self.ip_list = kwargs.pop('ip_list')
        self.clients = kwargs.pop('clients')
        self.ipset = kwargs.pop('ipset')
        self.lock = kwargs.pop('lock')
        self.block_list = kwargs.pop('block_list')
        super(UdpServer, self).__init__(*args, **kwargs)

    def do_read(self):
        try:
            data, address = self._socket.recvfrom(1024)
        except socket.error, err:
            if err[0] == socket.EWOULDBLOCK:
                return
            raise
        return data, address

    def sendto(self, *args):
        self._writelock.acquire()
        try:
            self.client.sendto(*args)
        finally:
            self._writelock.release()

    def ipset_add_ip(self, ip, device):
        self.lock.acquire()
        if ip not in self.ip_list:
            try:
                self.ip_list[ip] = set()
                self.ip_list[ip].add(device)
            except KeyError:
                pass
            try:
                self.ipset.add(IPSET_NAME, ip)
            except Exception, e:
                print e, ip, device
        else:
            self.ip_list[ip].add(device)
        self.lock.release()
        # self.lock.acquire()
        # self.lock.release()

    def ipset_remove_ip(self, ip, device):
        if ip in self.ip_list:
            self.lock.acquire()
            try:
                self.ip_list[ip].remove(device)
            except KeyError:
                pass
            if len(self.ip_list[ip]) == 0:
                try:
                    del self.ip_list[ip]
                    self.ipset.delete(IPSET_NAME, ip)
                except Exception, e:
                    print e, ip, device
            self.lock.release()
            # self.lock.acquire()
            # self.lock.release()

    def handle(self, datagram, address):
        """有datagram到来时会调用handle
        :可以根据address/uid来建立endpoint
        """
        host, port = address
        if host in self.block_list:
            return

        try:
            seed = ARC4.new(SEED_KEY)
            content = binascii.a2b_hex(datagram)
            device_id = seed.decrypt(content)
        except:
            print_error("解码错误, 原始数据%s, 发送ip为%s" % (datagram, host))
            return

        if host not in self.ip_list:
            if device_id in self.clients:
                old_ip = self.clients[device_id]['ip']
                if host != old_ip:
                    self.clients[device_id]['ip'] = host
                    self.clients[device_id]['timeout'] = time.time() + TIMEOUT
                    self.ipset_remove_ip(old_ip, device_id)
                    self.ipset_add_ip(host, device_id)
                else:
                    self.clients[device_id]['timeout'] = time.time() + TIMEOUT
        else:
            if device_id in self.clients:
                self.clients[device_id]['timeout'] = time.time() + TIMEOUT
        # source_address = '%s|||%d|||' % address
        # data = source_address + datagram
        # self.queue.put_nowait((data, (self.target_host, self.target_port)))


class UdpProducer(Process):
    def __init__(self, listener_host, listener_port, queue):

        Process.__init__(self)
        self.listener_host = listener_host
        self.listener_port = listener_port
        self.queue = queue
        self.server = None
        self.ipset = None
        self.lock = None
        self.kill = False
        self.ip_list = {}
        self.clients = {}
        self.block_list = set()

    def update_device(self):
        while not self.kill:
            device_dict = {}
            block_list = []
            try:
                block_list, device_dict = self.queue.get_nowait()
            except:
                pass
            if block_list and len(block_list) > 0:
                self.block_list.clear()
                for ip in block_list:
                    self.block_list.add(ip)
            if device_dict and len(device_dict) > 0:
                for k in self.clients.keys():
                    if k not in device_dict:
                        print_info("设备%s不在白名单,因此即将删除设备" % k)
                        try:
                            self.ipset_remove_ip(self.clients[k]['ip'], k)
                            del self.clients[k]
                        except Exception, e:
                            print e

            for k, v in device_dict.iteritems():
                    if k not in self.clients:
                        self.clients[k] = {'ip': v, 'timeout': time.time() + TIMEOUT}
                        try:
                            self.ipset_add_ip(v, k)
                        except Exception, e:
                            print e
            gevent.sleep(5)

    def ipset_add_ip(self, ip, device):
        self.lock.acquire()
        if ip not in self.ip_list:
            try:
                self.ip_list[ip] = set()
                self.ip_list[ip].add(device)
            except KeyError:
                pass
            try:
                self.ipset.add(IPSET_NAME, ip)
            except Exception, e:
                print e, ip, device
        else:
            self.ip_list[ip].add(device)
        self.lock.release()
        # self.lock.acquire()
        # self.lock.release()

    def ipset_remove_ip(self, ip, device):
        if ip in self.ip_list:
            self.lock.acquire()
            try:
                self.ip_list[ip].remove(device)
            except KeyError:
                pass
            if len(self.ip_list[ip]) == 0:
                try:
                    del self.ip_list[ip]
                    self.ipset.delete(IPSET_NAME, ip)
                except Exception, e:
                    print e, ip, device
            self.lock.release()
            # self.lock.acquire()
            # self.lock.release()

    def update_ip(self):
        """
        自动清除2小时没有心跳包的过期设备,
        删除设备列表,以及ip列表以及ipset
        :return:
        """
        while not self.kill:
            current_time = time.time()
            for k, v in self.clients.items():
                if v['timeout'] < current_time:
                    tmp_ip = v['ip']
                    print_info("设备%s[%s]超时,即将删除" % (k, tmp_ip))
                    try:
                        del self.clients[k]
                        self.ipset_remove_ip(tmp_ip, k)
                    except Exception, e:
                        print e
            print_info("当前共有合法ip %d" % len(self.ip_list))

            # 接下来验证ip数量是否一致
            ipset_ip_list = re.findall(r'\d+.\d+.\d+.\d+', str(self.ipset.list(IPSET_NAME)))
            ipset_ip_count = len(ipset_ip_list)
            ip_list_count = len(self.ip_list)
            # device_list_count = len(self.clients)
            #
            # ip_device = set()
            #
            # for v in self.ip_list.values():
            #     if len(v) > 1:
            #         print v
            #     for i in v:
            #         ip_device.add(i)
            # ip_device_count = len(ip_device)
            # if ip_device_count != device_list_count:
            #     print_info("ip列表设备数量[%d]与当前设备列表[%d]不对应,即将重新刷新" % (ip_device_count, device_list_count))
            if ipset_ip_count != ip_list_count:
                print_info("ipset列表[%d]与当前ip列表[%d]不对应,即将重新刷新" % (ipset_ip_count, ip_list_count))
                # self.lock.acquire()
                # self.ip_list = {}
                # self.clients = {}
                # self.lock.release()
            gevent.sleep(30)

    def terminate(self):
        """
        Terminate process; sends SIGTERM signal or uses TerminateProcess()
        """
        try:
            self.ipset.close()
            self.kill = True
            self.server.stop()
            self._popen.terminate()
        except:
            pass

    def run(self):
        print("UDP Server {0}-{1} at host {2} port {3}".format(multiprocessing.current_process().name,
                                                               str(os.getpid()),
                                                               self.listener_host, self.listener_port))
        self.ipset = ipset.IPSet()
        self.ip_list = {}
        self.block_list = set()
        self.clients = {}
        self.lock = Semaphore()
        self.kill = False
        try:
            self.ipset.destroy(IPSET_NAME)
            self.ipset.create(IPSET_NAME)
        except:
            pass
        try:
            self.ipset.flush(IPSET_NAME)
        except:
            pass
        gevent.spawn(self.update_device)
        gevent.spawn(self.update_ip)
        self.server = UdpServer(_udp_socket((self.listener_host, self.listener_port), reuse_addr=1),
                                ip_list=self.ip_list, clients=self.clients, ipset=self.ipset,
                                lock=self.lock, block_list=self.block_list)
        self.server.serve_forever()


class RedisProducer(Process):
    def __init__(self, redis_host, redis_port, queue):

        Process.__init__(self)
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.kill = False
        self.queue = queue
        self.redis_cli = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=0, socket_connect_timeout=60,
                                           socket_keepalive=True, retry_on_timeout=True)
        self.redis_block = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=1,
                                             socket_connect_timeout=60,
                                             socket_keepalive=True, retry_on_timeout=True)

    def fetch_list(self):
        more_device_list = {}
        device_dict = {}
        delete_list = set()
        try:
            white_list = self.redis_cli.keys("*")
            for device in white_list:
                tmp_device = device.split("||")
                if len(tmp_device) == 2 and bool(ipv4_re.search(tmp_device[1])):
                    if tmp_device[0] in device_dict:
                        if tmp_device[0] not in more_device_list:
                            more_device_list[tmp_device[0]] = 0
                        more_device_list[tmp_device[0]] += 1
                        if more_device_list[tmp_device[0]] > 3:
                            self.redis_block.setex(tmp_device[0], 60*60*2, tmp_device[1])
                            delete_list.add(device)
                    device_dict[tmp_device[0]] = tmp_device[1]
                else:
                    print_error("发现不合法序列号%s[%s],即将删除" % (tmp_device[0], tmp_device[1]))
                    self.redis_cli.delete(device)
            if len(delete_list) > 0:
                pipe = self.redis_cli.pipeline()
                for item in delete_list:
                    pipe.delete(item)
                pipe.execute()
            block_list = self.redis_block.keys("*")
            more_count = len(more_device_list)
            print_log("INFO", "当前在线设备为%d,重复设备数量%d" % (len(device_dict), more_count))
            if more_count > 0:
                print_warn("以下设备重复\n")
                print_warn(more_device_list)
            self.queue.put((block_list, device_dict))

        except redis.RedisError:
            print_error("redis服务器错误,等待10秒重新链接")
            self.redis_cli = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=0,
                                               socket_connect_timeout=60,
                                               socket_keepalive=True, retry_on_timeout=True)

            self.redis_block = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=1,
                                                 socket_connect_timeout=60,
                                                 socket_keepalive=True, retry_on_timeout=True)
        except Exception, e:
            print_error(e.message)

    def terminate(self):
        """
        Terminate process; sends SIGTERM signal or uses TerminateProcess()
        """
        try:
            self.kill = True
            self.queue.clear()
            self.redis_cli.connection_pool.disconnect()
            self.redis_block.connection_pool.disconnect()
            time.sleep(5)
            self._popen.terminate()
        except:
            pass

    def run(self):
        print("redis client {0}-{1} at host {2} port {3}".format(multiprocessing.current_process().name,
                                                                 str(os.getpid()), self.redis_host, self.redis_port))
        self.kill = False
        while not self.kill:
            self.fetch_list()
            time.sleep(10)


class HeartBeatManager(object):

    def __init__(self, redis_host, redis_port, listener_host, listener_port):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.listener_host = listener_host
        self.listener_port = listener_port
        self.queue = PQueue()
        self.processed = []
        self.alive = True
        self.killing = True

    def exit_handler(self, signum, frame):
        self.alive = False
        if self.killing:
            self.killing = False
            print_info('catched singal: %d' % signum)
            for i in range(len(self.processed)):
                try:
                    if self.processed[i].is_alive():
                        print_info("exit process %s-%d" % (self.processed[i].name, self.processed[i].pid))
                        self.processed[i].terminate()
                except:
                    pass

            print_info("exit main process")
            time.sleep(10)
            sys.exit(1)

    def run(self):
        signal.signal(signal.SIGTERM, self.exit_handler)
        # redis更新进程
        redis_process = RedisProducer(self.redis_host, self.redis_port, self.queue)
        self.processed.append(redis_process)
        self.processed[0].start()

        worker_process = UdpProducer(self.listener_host, self.listener_port, self.queue)
        self.processed.append(worker_process)
        self.processed[1].start()

        # # 监控进程并重启进程
        while self.alive:
            if not redis_process.is_alive():
                print_error("redis process %d was dead, will restart it!" % redis_process.pid)
                try:
                    redis_process.terminate()
                except:
                    pass
                finally:
                    redis_process = RedisProducer(self.redis_host, self.redis_port, self.queue)
                    redis_process.start()

            if not worker_process.is_alive():
                print_error("worker process %d was dead, will restart it!" % worker_process.pid)
                try:
                    worker_process.terminate()
                except:
                    pass
                finally:
                    worker_process = UdpProducer(self.listener_host, self.listener_port, self.queue)
                    worker_process.start()

            time.sleep(10)


def _udp_socket(address, backlog=5000, reuse_addr=None):
    # we want gevent.socket.socket here
    sock = socket.socket(family=_socket.AF_INET, type=_socket.SOCK_DGRAM)
    if reuse_addr is not None:
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEPORT, reuse_addr)
    try:
        sock.bind(address)
    except _socket.error:
        ex = sys.exc_info()[1]
        strerror = getattr(ex, 'strerror', None)
        if strerror is not None:
            ex.strerror = strerror + ': ' + repr(address)
        raise
    return sock
