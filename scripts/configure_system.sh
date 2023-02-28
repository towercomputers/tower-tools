#!/bin/bash

ROOT_PASSWORD=$1
USERNAME=$2
PASSWORD=$3
LANG=$4
TIMEZONE=$5
KEYMAP=$6

# set locales
ln -sf /usr/share/zoneinfo/$TIMEZONE /etc/localtime
hwclock --systohc
cp /etc/locale.gen /etc/locale.gen.list
echo "$LANG UTF-8" > /etc/locale.gen
locale-gen
echo "LANG=$LANG" > /etc/locale.conf
echo "KEYMAP=$KEYMAP" > /etc/vconsole.conf
# set hostname
echo "tower" > /etc/hostname
# change root password
usermod --password $(echo $ROOT_PASSWORD | openssl passwd -1 -stdin) root
# create first user
useradd -m $USERNAME -p $(echo $PASSWORD | openssl passwd -1 -stdin)
echo "tower ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/01_tower_nopasswd
usermod -aG docker tower
# install boot loader
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
grub-mkconfig -o /boot/grub/grub.cfg
# activate startx
echo "exec startlxde" > /home/$USERNAME/.xinitrc
# enable services
systemctl enable iwd.service
systemctl enable dhcpcd.service
systemctl enable avahi-daemon.service
systemctl enable docker.service

#install nxagent
#cd /home/tower && \
#    && sudo -u tower -- git clone https://aur.archlinux.org/nx.git \
#    && cd nx \
#    && sudo -u tower -- makepkg -s -i -r -c --noconfirm \
#    && cd .. && rm -rf nx