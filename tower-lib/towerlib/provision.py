import os
import secrets
import logging
from datetime import datetime

from passlib.hash import sha512_crypt
from sh import ssh_keygen, xz, ssh, cp, dd
from rich.prompt import Confirm
from rich.text import Text

from towerlib import utils
from towerlib import buildhost
from towerlib import sshconf

logger = logging.getLogger('tower')

class MissingEnvironmentValue(Exception):
    pass

def check_environment_value(key, value):
    if not value:
        raise MissingEnvironmentValue(f"Impossible to determine the {key}. Please use the option --{key}.")

def generate_key_pair(name):
    os.makedirs(os.path.join(sshconf.TOWER_DIR, 'ssh'), exist_ok=True)
    key_path = os.path.join(sshconf.TOWER_DIR, 'ssh', f'{name}')
    if os.path.exists(key_path):
        os.remove(key_path)
        os.remove(f'{key_path}.pub')
    ssh_keygen('-t', 'ed25519', '-C', name, '-f', key_path, '-N', "")
    return f'{key_path}.pub', key_path

def generate_luks_key(name):
    keys_path = os.path.join(sshconf.TOWER_DIR, 'luks', f"{name}_crypto_keyfile.bin")
    os.makedirs(os.path.dirname(keys_path), exist_ok=True)
    dd('if=/dev/urandom', f'of={keys_path}', 'bs=512', 'count=4')

@utils.clitask("Preparing host configuration...")
def prepare_host_config(args):
    name = args.name[0]
    # public key for ssh
    check_environment_value('public-key-path', args.public_key_path)
    with open(args.public_key_path) as f:
        public_key = f.read().strip()
    # generate random password
    password = secrets.token_urlsafe(16)
    # gather locale informations
    keyboard_layout, keyboard_variant = utils.get_keymap()
    if args.keyboard_layout:
        keyboard_layout = args.keyboard_layout
    if args.keyboard_variant:
        keyboard_variant = args.keyboard_variant
    timezone = args.timezone or utils.get_timezone()
    lang = args.lang or utils.get_lang()
    # determine if online
    online = 'true' if args.online or name == sshconf.ROUTER_HOSTNAME else 'false'
    if name == sshconf.ROUTER_HOSTNAME:
        wlan_ssid = args.wlan_ssid
        wlan_shared_key = utils.derive_wlan_key(args.wlan_ssid, args.wlan_password)
    else:
        wlan_ssid = ""
        wlan_shared_key = ""
    # determine thinclient IP and network
    if name == sshconf.ROUTER_HOSTNAME or online == "true":
        tower_network = sshconf.TOWER_NETWORK_ONLINE
        thin_client_ip = sshconf.THIN_CLIENT_IP_ETH0
    else:
        tower_network = sshconf.TOWER_NETWORK_OFFLINE
        thin_client_ip = sshconf.THIN_CLIENT_IP_ETH1
    if name == sshconf.ROUTER_HOSTNAME:
        host_ip =sshconf.ROUTER_IP
    else:
        host_ip = sshconf.get_next_host_ip(tower_network)
    # return complete configuration
    return {
        'HOSTNAME': name,
        'USERNAME': sshconf.DEFAULT_SSH_USER,
        'PUBLIC_KEY': public_key,
        'PASSWORD': password,
        'PASSWORD_HASH': sha512_crypt.hash(password),
        'KEYBOARD_LAYOUT': keyboard_layout,
        'KEYBOARD_VARIANT': keyboard_variant,
        'TIMEZONE': timezone,
        'LANG': lang,
        'ONLINE': online,
        'WLAN_SSID': wlan_ssid,
        'WLAN_SHARED_KEY': wlan_shared_key,
        'THIN_CLIENT_IP': thin_client_ip,
        'TOWER_NETWORK': tower_network,
        'STATIC_HOST_IP': host_ip,
        'ROUTER_IP': sshconf.ROUTER_IP,
        'INSTALLATION_TYPE': "install",
    }

@utils.clitask("Decompressing {0}...", sudo=True)
def decompress_image(image_path):
    out_file = image_path.replace('.xz', '')
    tmp_file = os.path.join('/tmp', os.path.basename(out_file))
    xz('--stdout', '-d', image_path, _out=tmp_file)
    cp(tmp_file, out_file)
    return out_file

def prepare_host_image(image_arg):
    image_path = image_arg if image_arg and os.path.isfile(image_arg) else utils.find_host_image()
    if image_path:
        ext = image_path.split(".").pop()
        if ext == 'xz': # TODO: support more formats
            image_path = decompress_image(image_path)
    return image_path

def prepare_provision(args):
    if args.update:
        # use existing key pair
        private_key_path = os.path.join(sshconf.TOWER_DIR, 'ssh', f'{args.name[0]}')
        # load configuration
        conf_path = os.path.join(sshconf.TOWER_DIR, 'hosts', f"{args.name[0]}.env")
        with open(conf_path, 'r') as f:
            config_str = f.read()
        host_config = {}
        for line in config_str.strip().split("\n"):
            key = line[0:line.index('=')]
            value = line[line.index('=') + 2:-1]
            host_config[key] = value
        host_config['INSTALLATION_TYPE'] = "update"
    else:
        # generate key pair
        if not args.public_key_path:
            args.public_key_path, private_key_path = generate_key_pair(args.name[0])
        # generate luks key
        generate_luks_key(args.name[0])
        # generate host configuration
        host_config = prepare_host_config(args)
    # determine target device
    boot_device = args.boot_device or utils.select_boot_device()
    check_environment_value('boot-device', boot_device)
    # find TowerOS-Host image
    image_path = prepare_host_image(args.image)
    check_environment_value('image', image_path)
    # return everything needed to provision the host
    return image_path, boot_device, host_config, private_key_path

@utils.clitask("Saving host configuration in {0}...")
def save_config_file(config_path, config_str):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        f.write(config_str)
    os.chmod(config_path, 0o600)

def save_host_config(config):
    config_filename = f"{config['HOSTNAME']}.env"
    config_path = os.path.join(sshconf.TOWER_DIR, 'hosts', config_filename)
    config_str = "\n".join([f"{key}='{value}'" for key, value in config.items()])
    save_config_file(config_path, config_str)
    
@utils.clitask("Provisioning {0}...", timer_message="Host provisioned in {0}.", task_parent=True)
def provision(name, args):
    image_path, boot_device, host_config, private_key_path = prepare_provision(args)
    confirm_message = f"Are you sure you want to completely wipe the boot device `{boot_device}` plugged into the Thin Client "
    confirm_message += f"and the root device plugged into the host `{name}` and install TowerOS-Host on them?"
    confirm_text = Text(confirm_message, style='red')
    if args.no_confirm or Confirm.ask(confirm_text):
        if not args.update:
            save_host_config(host_config)
        del(host_config['PASSWORD'])
        buildhost.burn_image(image_path, boot_device, host_config, args.zero_device)
        if not args.update:
            sshconf.update_config(name, host_config['STATIC_HOST_IP'], private_key_path)
        sshconf.wait_for_host_sshd(name, host_config['STATIC_HOST_IP'])
        utils.menu.prepare_xfce_menu()
        logger.info(f"Host ready with IP: {host_config['STATIC_HOST_IP']}")
        logger.info(f"Access the host `{name}` with the command `$ ssh {name}`.")
        logger.info(f"Install a package on `{name}` with the command `$ tower install {name} <package-name>`")
        logger.info(f"Run a GUI application on `{name}` with the command `$ tower run {name} <package-name>`")
        logger.info(f"WARNING: For security reasons, make sure to remove the external device containing the boot partition from the host.")

@utils.clitask("Updating wlan credentials...")
def wlan_connect(ssid, password):
    psk = utils.derive_wlan_key(ssid, password)
    supplicant_path = "/etc/wpa_supplicant/wpa_supplicant.conf"
    cmd  = f"sudo echo 'network={{' | sudo tee {supplicant_path} && "
    cmd += f"sudo echo '    ssid=\"{ssid}\"'  | sudo tee -a  {supplicant_path} && "
    cmd += f"sudo echo '    psk={psk}'  | sudo tee -a {supplicant_path} && "
    cmd += f"sudo echo '}}' | sudo tee -a {supplicant_path}"
    ssh(sshconf.ROUTER_HOSTNAME, cmd)
    ssh(sshconf.ROUTER_HOSTNAME, "sudo rc-service wpa_supplicant restart")
