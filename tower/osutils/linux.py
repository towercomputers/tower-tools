import configparser
from io import StringIO
import os
import json

import sh
from sh import lsblk, mount as _mount, umount, timedatectl, iwconfig, localectl, iw

def get_device_list():
    buf = StringIO()
    lsblk('-J', '-T', '-d', _out=buf)
    result = json.loads(buf.getvalue())
    return [f"/dev/{e['name']}" for e in result['blockdevices']]

def mount(device):
    mountpoint = os.path.expanduser('~/towersd')
    if not os.path.exists(mountpoint):
        os.makedirs(mountpoint)
    with sh.contrib.sudo:
        # first partition where to put files
        _mount('-o', f'gid={os.getgid()},uid={os.getuid()}', f'{device}1', mountpoint) 

def get_mount_point(device):
    buf = StringIO()
    lsblk('-J', '-T', device, _out=buf)
    result = json.loads(buf.getvalue())
    return result['blockdevices'][0]['children'][0]['mountpoint'] # first partition where to put files

def unmount(device):
    mountpoint = get_mount_point(device)
    if mountpoint not in [None, ""]:
        umount(mountpoint)

def rpi_imager_path():
    return "/usr/bin/rpi-imager"

def disable_rpi_image_ejection():
    conf_path = os.path.join(os.path.expanduser('~'), '.config/', 'Raspberry Pi/', 'Imager.conf')
    conf_dir = os.path.dirname(conf_path)
    config = configparser.ConfigParser()
    if os.path.exists(conf_path):
        config.read(conf_path)
    config[configparser.DEFAULTSECT]['eject'] = 'false'
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    with open(conf_path, 'w') as f:
        config.write(f)

def dd(image, device):
    if get_mount_point(device) is not None:
        unmount(device)
    dd(f"if={image}",f"of={device}", "bs=8m", "oflag=sync")

def scan_wifi_countries():
    buf = StringIO()
    with sh.contrib.sudo: # TODO: find no-sudo way
        iw('dev', 'wlan0', 'scan', _out=buf)
    result = buf.getvalue()
    bss = result.split('BSS ')
    wifis= {}
    for info in bss:
        if info.find("SSID: ") != -1:
            ssid = info.split('SSID: ')[1].split('\t')[0].strip()
            cc = '--'
            if info.find("Country: ") != -1:
                cc = info.split("Country: ")[1].split('\t')[0]
            if ssid not in wifis or wifis[ssid] == '--':
                wifis[ssid] = cc
    return wifis

def get_connected_ssid():
    try:
        buf = StringIO()
        iwconfig(_out=buf)
        result = buf.getvalue()
        ssid = result.split('ESSID:"')[1].split('"')[0]
        return ssid
    except: # no need to be curious here
        return None

def get_ssid_password(ssid):
    try:
        network_manager_conf_path = f'/etc/NetworkManager/system-connections/{ssid}.nmconnection'
        if os.path.exists(network_manager_conf_path):
            wlan_conf = configparser.ConfigParser()
            wlan_conf.read(network_manager_conf_path)
            password = wlan_conf['wifi-security']['psk']
            return password
        wpa_supplicant_path = '/etc/wpa_supplicant/wpa_supplicant.conf'
        if os.path.exists(wpa_supplicant_path):
            with open(wpa_supplicant_path) as f:
                wlan_conf = f.read()
            password = wlan_conf.split('psk=')[1].split('\n')[0].strip().replace('"', '')
            return password
        return None
    except: # no need to be curious here
        return None

def get_timezone():
    buf = StringIO()
    timedatectl(_out=buf)
    result = buf.getvalue()
    return result.split("Time zone:")[1].strip().split(" ")[0].strip()

def get_keymap():
    buf = StringIO()
    localectl(_out=buf)
    result = buf.getvalue()
    return result.split("X11 Layout:")[1].strip().split(" ")[0].strip()