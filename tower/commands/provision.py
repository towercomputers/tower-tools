from argparse import ArgumentParser
import ipaddress
import os
import re
import sys

from tower.configs import default_config_dir, create_computer_config, get_tower_config, MissingConfigValue
from tower.imager import burn_image

def check_args(args, parser_error):
    if re.match(r'/^(?![0-9]{1,15}$)[a-zA-Z0-9-]{1,15}$/', args.name[0]):
        parser_error(message="Computer name invalid. Must be between one and 15 alphanumeric chars.")

    config_dir = args.config_dir or default_config_dir()
    config_file = os.path.join(config_dir, f'{args.name}.ini')
    if os.path.exists(config_file):
        parser_error("Computer name already used.")

    if args.sd_card and not os.path.exists(args.sd_card):
        parser_error("sd-card path invalid.") # TODO: check is a disk
    
    if args.public_key_path:
        if not arg.private_key_path :
            parser_error("You must provide both keys or none.")
        if not os.path.exists(args.public_key_path):
            parser_error("public_key path invalid.")
    
    if args.private_key_path:
        if not arg.public_key_path :
            parser_error("You must provide both keys or none.")
        if not os.path.exists(args.private_key_path):
            parser_error("private_key path invalid.")
    
    # TODO: check format for keymap, timezone, and wlan-country


def execute(args):
    tower_config = get_tower_config(args.config_dir)
    try:
        computer_config = create_computer_config(args)
    except MissingConfigValue as e:
        sys.exit(e)
    burn_image(dict(computer_config) | dict(tower_config))