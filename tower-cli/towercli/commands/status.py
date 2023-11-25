import json

from towerlib import sshconf

def add_args(argparser):
    argparser.add_parser(
        'status',
        help="Check the status of all hosts in the Tower system."
    )

# pylint: disable=unused-argument
def check_args(args, parser_error):
    pass

# pylint: disable=unused-argument
def execute(args):
    print(json.dumps(sshconf.status(), indent=4))
