import argparse
import logging
import sys
import pystuntest

def make_argument_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '-H', '--stun-host',
        default=pystuntest.STUN_SERVERS,
        help='STUN host to use'
    )
    parser.add_argument(
        '-P', '--stun-port', type=int,
        default=pystuntest.DEFAULTS['stun_port'],
        help='STUN host port to use'
    )
    parser.add_argument(
        '-i', '--source-ip',
        default=pystuntest.DEFAULTS['source_ip'],
        help='network interface for client'
    )
    parser.add_argument(
        '-p', '--source-port', type=int,
        default=pystuntest.DEFAULTS['source_port'],
        help='port to listen on for client'
    )

    parser.add_argument('--version', action='version', version=pystuntest.__version__)

    return parser


def main():
    try:
        options = make_argument_parser().parse_args()

        if options.debug:
            logging.basicConfig()
            pystuntest.log.setLevel(logging.DEBUG)

        mapping_type, filtering_type, external_ip, external_port = pystuntest.get_nat_test(
            source_ip=options.source_ip,
            source_port=options.source_port,
            stun_host=options.stun_host,
            stun_port=options.stun_port
        )

        print('Mapping Type:', mapping_type)
        print('Filtering Type:', filtering_type)
        print('External IP:', external_ip)
        print('External Port:', external_port)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    main()