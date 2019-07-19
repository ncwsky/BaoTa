#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
download_Url='http://39.105.93.185'
pluginPath=/www/server/panel/plugin/sshkey

Install_sshkey()
{
   	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/sshkey_main.py $download_Url/sshkey/sshkey_main.py -T 5
	wget -O $pluginPath/index.html $download_Url/sshkey/index.html -T 5
	wget -O $pluginPath/info.json $download_Url/sshkey/info.json -T 5
	wget -O $pluginPath/icon.png $download_Url/sshkey/icon.png -T 5
	\cp -a -r /www/server/panel/plugin/sshkey/icon.png /www/server/panel/BTPanel/static/img/soft_ico/ico-sshkey.png
	echo '安装完成' > $install_tmp
}

Uninstall_sshkey()
{
	rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_sshkey
elif  [ "${1}" == 'update' ];then
	Install_sshkey
elif [ "${1}" == 'uninstall' ];then
	Uninstall_sshkey
fi
