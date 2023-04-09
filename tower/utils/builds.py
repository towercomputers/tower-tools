import os
import logging
import glob

from sh import shasum

from tower.utils import network
from tower.utils.decorators import clitask

logger = logging.getLogger('tower')

class InvalidChecksum(Exception):
    pass

REQUIRED_BUILDS = {
    "arch-linux-arm": {
        "filename": "ArchLinuxARM-rpi-armv7-latest.tar.gz",
        "url": "http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-armv7-latest.tar.gz",
        "checksum": "65472324ff51bde690379c67b7c5e299e532e63747bf1f71d20552c63708e1b0"
    },
    "nx-armv7h": {
        "filename": "nx-armv7h.tar.gz",
        "url": "https://drive.google.com/uc?export=download&confirm=yes&id=17jHstO67SGuZoINPBcU16StwsJlZ0gpC",
        "checksum": "1fca33faa926d03bcdd52d0f0d5cbe2bd16a5f3b1cddcf7d1747c82bacebde1c"
    },
    "nx-x86_64": {
        "filename": "nx-x86_64.tar.gz",
        "url": "https://drive.google.com/uc?export=download&confirm=yes&id=1xuieznP6xCAxspWY9acOyIFEH21U8YRT",
        "checksum": "c3528a4b494260ab6473a9af6b5e95546310f84ca51cdc21127b029e3d0b4d6a"
    }
}

def init_builds_dir(args_builds_dir):
    builds_dir = args_builds_dir
    # if not provided check if builds is in ./ or in ~/.cache/tower/
    if not builds_dir:
        builds_dir = os.path.join(os.getcwd(), 'dist')
        if os.path.isdir(builds_dir):
            return builds_dir
        builds_dir = os.path.join(os.getcwd(), 'builds')
        if os.path.isdir(builds_dir):
            return builds_dir
        builds_dir = os.path.join(os.path.expanduser('~'), '.cache', 'tower', 'builds')
        if os.path.isdir(builds_dir):
            return builds_dir
    # if not exists, create it
    if not os.path.isdir(builds_dir):
        os.makedirs(builds_dir)
    return builds_dir

def sha_sum(file_path):
    res = shasum('-a256', file_path)
    return res.split(" ")[0].strip()

@clitask("Checking {0} checksum...")
def chek_sha_sum(file_path, checksum):
    file_checksum = sha_sum(file_path)
    if file_checksum != checksum:
        raise InvalidChecksum(f"Invalid checksum for {file_path}: {checksum} != {file_checksum}")

def prepare_required_build(build_name, builds_dir):
    build = REQUIRED_BUILDS[build_name]
    file_path = os.path.join(builds_dir, build["filename"])
    if not os.path.isfile(file_path):
        logger.info(f'{build["filename"]} not found in builds directory.')
        network.download_file(build["url"], file_path)
    chek_sha_sum(file_path, build["checksum"])
    return file_path

def find_host_image():
    image_path = None
    builds_dirs = [
        os.path.join(os.getcwd(), 'dist'),
        os.path.join(os.getcwd(), 'builds'),
        os.path.join(os.path.expanduser('~'), '.cache', 'tower', 'builds')
    ]
    for builds_dir in builds_dirs:
        if os.path.isdir(builds_dir):
            host_images = glob.glob(os.path.join(builds_dir, 'towerospi-*.xz'))
            host_images += glob.glob(os.path.join(builds_dir, 'towerospi-*.img'))
            if host_images:
                image_path = host_images.pop()
                break
    return image_path