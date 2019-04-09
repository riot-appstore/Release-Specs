#! /usr/bin/env python3
# Copyright (C) 2018 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import sys
import os

import tqdm

class TestSpec:
    PORT = 1337
    COUNT = 1000
    PAYLOAD_SIZE = 1024
    DELAY = 1000   # ms
    ERROR_TOLERANCE = 5     # %
    ADDRESS = "dest"

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def check(self, result):
        """Return the result if it is valid, or fail."""
        assert result.packet_loss < self.ERROR_TOLERANCE
        assert result.src_buf_empty
        assert result.dst_buf_empty

        return result


class GhostNode:
    def get_ip_addr(self):
        return "fe80::bd:b7ec"


SPECS = {'normal': TestSpec(),
         'compression': TestSpec(PORT=61616),
         'nonexistant': TestSpec(ERROR_TOLERANCE=100, PAYLOAD_SIZE=8,
                                 ADDRESS="ghost", DELAY=0),
         'empty': TestSpec(PAYLOAD_SIZE=0, COUNT=10, INTERVAL=100),
        }


def run_spec(nodes, spec):
    dest_ip = nodes[spec.ADDRESS].get_ip_addr()

    return udp_send(nodes['source'], nodes['dest'], dest_ip, spec.PORT,
                    spec.COUNT, spec.PAYLOAD_SIZE, spec.DELAY)


def run_tasks(riotbase, runs=1):
    os.chdir(os.path.join(riotbase, "tests/gnrc_udp"))

    node_specs = [IoTLABNode(site="lille", extra_modules=["gnrc_pktbuf_cmd"]),
                  IoTLABNode(site="lille", extra_modules=["gnrc_pktbuf_cmd"])]

    with IoTLABExperiment("RIOT-release-test-06-01", node_specs) as exp:
        addrs = exp.nodes_addresses
        iotlab_cmd = "make IOTLAB_NODE={} BOARD=iotlab-m3 term"
        nodes = {'source': SixLoWPANNode(iotlab_cmd.format(addrs[0])),
                 'dest': SixLoWPANNode(iotlab_cmd.format(addrs[1])),
                 'ghost': GhostNode()
                }
        results = []

        spec_progress = tqdm.tqdm(SPECS.items(), unit="Specs")

        results = ((spec_name, spec_progress.set_description(
                                "Spec: {}".format(spec_name))
                              or spec.check(run_spec(nodes, spec)))
                   for spec_name, spec in spec_progress)

        print_results(results)

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../", "testutils"))
    from iotlab import IoTLABNode, IoTLABExperiment, IoTLABExperimentError
    from common import argparser, SixLoWPANNode, udp_send, print_results

    args = argparser.parse_args()

    try:
        run_tasks(**vars(args))
    except IoTLABExperimentError as e:
        print(str(e))
        print("Can't start experiment")
    except AssertionError as e:
        print("FAILED")
        print(str(e))
