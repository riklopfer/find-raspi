import argparse
import collections
import logging
import os
import re
import sys
from typing import Iterable, List, Optional

from find_sshable import net, sshconf

_program_name = "find-sshable"
logger = logging.getLogger(_program_name)


def _update_names(hosts: List[net.Host], host_prefix: str) -> List[net.Host]:
    name_count = collections.Counter()

    updated = []
    for host in hosts:
        if name_count[host.name] > 0:
            suffix = f"-{name_count[host.name]}"
        else:
            suffix = ""
        updated.append(net.Host(name=f"{host_prefix}{host.name}{suffix}", ip=host.ip))
        name_count[host.name] += 1

    return updated


def add_to_ssh_conf(hosts: Iterable[net.Host],
                    ssh_user: Optional[str] = None,
                    host_prefix: Optional[str] = 'find-sshable.'):
    if hosts is not None:
        hosts = list(hosts)

    assert hosts, "Addrs is empty"

    hosts = _update_names(hosts, host_prefix)

    print(
        "\nDevices will be added to your ssh config as follows\n"
        "{}".format("\n".join("\t".join([h.name, str(h.ip)])
                              for h in hosts))
    )

    # add it to your ssh config
    ssh_config_path = os.path.join(os.getenv("HOME", "/"), ".ssh", "config")

    host_entries = [sshconf.HostEntry(h.name, User=ssh_user, HostName=h.ip_str) for h in hosts]
    sshconf.update_found_hosts(host_entries, ssh_config_path)


def main(argv):
    parser = argparse.ArgumentParser(prog=_program_name)

    parser.add_argument('--host-pattern',
                        help="Only return hosts whose hostname contain this regex (search not match)",
                        type=re.compile, default=None)
    parser.add_argument('--passive',
                        help="Do not check for ssh auth methods -- just an open port",
                        action='store_true')

    ssh_opt = parser.add_argument_group('SSH Config Options')
    ssh_opt.add_argument('--update-ssh-config',
                         help="Update ssh config with entries for the sshable hosts",
                         action='store_true')
    ssh_opt.add_argument('--host-prefix',
                         help="Prepend this to the each host entry added to ssh config (--update-ssh-config)",
                         type=str, default='find-sshable.')
    ssh_opt.add_argument('--ssh-user',
                         help="User for host entries added to ssh config (--update-ssh-config)",
                         type=str, default=None)

    parser.add_argument('-v', help="verbosity",
                        action='count', default=0)

    args = parser.parse_args(argv[1:])
    if args.v > 1:
        logging.basicConfig(level=logging.DEBUG)
    elif args.v > 0:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    update_ssh_conf = args.update_ssh_config
    host_pattern = args.host_pattern
    ssh_user = args.ssh_user
    host_prefix = args.host_prefix
    passive = args.passive

    if not update_ssh_conf:
        logger.info("`--update-ssh-config` not specified; will not create ssh.conf entries")

    pi_addrs = net.find_sshable(host_pattern=host_pattern, passive=passive)
    if pi_addrs:
        print(
            "\nFound {} devices...\n"
            "{}".format(len(pi_addrs), "\n".join(map(str, pi_addrs)))
        )

        if update_ssh_conf:
            add_to_ssh_conf(pi_addrs, ssh_user=ssh_user, host_prefix=host_prefix)
    else:
        print("No SSH-able devices found.")


def main_no_args():
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        return 1


if __name__ == '__main__':
    sys.exit(main_no_args())
