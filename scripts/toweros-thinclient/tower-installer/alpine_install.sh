#!/bin/bash

set -e
set -x


ROOT_PASSWORD=$1
USERNAME=$2
PASSWORD=$3
LANG=$4
TIMEZONE=$5
KEYBOARD_LAYOUT=$6
KEYBOARD_VARIANT=$7
TARGET_DRIVE=$8

ROOT_PASSWORD="tower"
USERNAME="tower"
PASSWORD="tower"
LANG="us"
TIMEZONE="Europe/Paris"
KEYBOARD_LAYOUT="us"
KEYBOARD_VARIANT="us"
TARGET_DRIVE="/dev/sda"

apk add sudo dhcpcd wpa_supplicant avahi iptables

# change root password
echo -e "$ROOT_PASSWORD\n$ROOT_PASSWORD" | passwd root
# create first user
adduser -D "$USERNAME" "$USERNAME"
echo -e "$PASSWORD\n$PASSWORD" | passwd "$USERNAME"

setup-timezone "$TIMEZONE"
setup-keymap "$KEYBOARD_LAYOUT" "$KEYBOARD_VARIANT"
setup-hostname -n tower

rc-update add dhcpcd
rc-update add avahi-daemon
rc-update add iptables
rc-update add wpa_supplicant boot

yes | setup-disk -m sys "$TARGET_DRIVE"

ROOT_PARTITION=$(ls $TARGET_DRIVE*3)
mount "$ROOT_PARTITION" /mnt

mkdir -p "/home/$USERNAME"
mkdir "/home/$USERNAME/.ssh"
mkdir "/home/$USERNAME/.cache"
mkdir "/home/$USERNAME/.config"
chown -R "$USERNAME:$USERNAME" "/home/$USERNAME"

echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" > /mnt/etc/sudoers.d/01_tower_nopasswd

cat <<EOF > /mnt/etc/network/interfaces
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF

# on first boot as root
# ip link set wlan0 up
# wpa_passphrase 'ExampleWifiSSID' 'ExampleWifiPassword' > /etc/wpa_supplicant/wpa_supplicant.conf
# wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
# udhcpc -i wlan0
# setup-apkrepos
# apk update
# uncomment community repo in /etc/apk/repositories