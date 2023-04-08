import argparse
import os

from tower import toweros, towerospi, utils
from tower.clis import clilogger

def parse_arguments():
    parser = argparse.ArgumentParser(description="""Generate TowerOS and TowerOS PI images""")
    parser.add_argument(
        '-v', '--verbose',
        help="""Set log level to DEBUG.""",
        required=False,
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--quiet',
        help="""Set log level to ERROR.""",
        required=False,
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--builds-dir',
        help="""Directory containing builds necessary to build an image.""",
        required=False,
    )
    subparser = parser.add_subparsers(
        dest='image_name', 
        required=True, 
        help="Use `build-tower-image {thinclient|host} --help` to get options list for each image."
    )
    thinclient_parser = subparser.add_parser(
        'thinclient',
        help="""Command used to generate thinclient image"""
    )
    host_parser = subparser.add_parser(
        'host',
        help="""Command used to generate host image."""
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()
    clilogger.initialize(args.verbose, args.quiet)
    builds_dir = utils.init_builds_dir(args.builds_dir)
    if args.image_name == 'host':
        towerospi.build_image(builds_dir)
    elif args.image_name == 'thinclient':
        toweros.build_image(builds_dir)


