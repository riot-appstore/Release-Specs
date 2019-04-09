from collections import namedtuple
import argparse

from testutils import Board
from mixins import GNRC, GNRC_UDP,PktBuf
from time import sleep


Result = namedtuple("Result", "packet_loss src_buf_empty dst_buf_empty")

#Declare node
class SixLoWPANNode(Board, GNRC, GNRC_UDP, PktBuf):
    pass


def print_results(results_iter):
    results = list(results_iter)
    print("")
    print("Summary of {packet losses, source pktbuf sanity, dest pktbuf sanity}:")
    for spec, r in results:
        print("Run {}: {}".format(spec, r))
    print("")

def udp_send(source, dest, ip_dest, port, count, payload_size, delay):
    source.reboot()
    dest.reboot()

    dest.udp_server_start(port)
    source.udp_send(ip_dest, port, payload_size, count, delay)
    packet_loss = dest.udp_server_check_output(count, delay)
    dest.udp_server_stop()

    return Result(packet_loss, source.is_empty(), dest.is_empty())


argparser = argparse.ArgumentParser()
argparser.add_argument("--runs", "-n", help="Number of runs", type=int,
                       default=1)
argparser.add_argument("riotbase", help="Location of RIOT directory")
