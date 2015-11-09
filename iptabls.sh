iptables -A OUTPUT -p udp --sport 9901 -j NFQUEUE --queue-balance 100:120 --queue-cpu-fanout
iptables -A OUTPUT -p udp --sport 9902 -j NFQUEUE --queue-balance 200:220 --queue-cpu-fanout
iptables -A OUTPUT -p udp --sport 9903 -j NFQUEUE --queue-balance 300:320 --queue-cpu-fanout
iptables -A OUTPUT -p udp --sport 9904 -j NFQUEUE --queue-balance 400:420 --queue-cpu-fanout
iptables -A OUTPUT -p udp --sport 9905 -j NFQUEUE --queue-balance 500:520 --queue-cpu-fanout
iptables -A OUTPUT -p udp --sport 9906 -j NFQUEUE --queue-balance 600:620 --queue-cpu-fanout