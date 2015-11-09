apt-get install build-essential python-dev libnetfilter-queue-dev
pip install https://github.com/fqrouter/python-netfilterqueue/archive/master.zip
pip install gevent
pip install dpkt
# sudo iptables -A OUTPUT -p udp --sport 9000 -j NFQUEUE --queue-num 10
sudo sudo tcpdump -vvv -i ethn -en -s 0 -XX udp port 8014
sudo cat /proc/net/netfilter/nfnetlink_queue
