#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
public_file=/www/server/panel/install/public.sh
download_Url='http://39.105.93.185'
pluginPath=/www/server/panel/plugin/ossfs

Install_ossfs()
{
if [ ! -f "/usr/local/bin/ossfs" ];then
	ubuntu16Pack="ossfs_1.80.5_ubuntu16.04_amd64.deb"
	if [ -f "/usr/bin/yum" ] && [ -f "/usr/bin/rpm" ]; then
		centos_version=$(cat /etc/redhat-release | grep ' 7.' | grep -i centos)
		if [ "${centos_version}" != '' ]; then
			centosPack="ossfs_1.80.5_centos7.0_x86_64.rpm"
		else
			centosPack="ossfs_1.80.5_centos6.5_x86_64.rpm"
		fi
		wget -O ${centosPack} ${download_Url}/${centosPack}
		yum localinstall ${centosPack} -y
		rm -f ${centosPack}
	elif [ -f "/usr/bin/apt-get" ]; then
		ubuntu16=$(cat /etc/issue|awk '{print $2}'|grep -oE '16.04')
		if [ "${ubuntu16}" != '' ]; then
			wget -O ${ubuntu16Pack} ${download_Url}/${ubuntu16Pack}
			apt-get update
			apt-get install gdebi-core -y
			gdebi ${ubuntu16Pack} -n
			rm -f ${ubuntu16Pack}
		else
			exit;
		fi
	fi
fi
   	mkdir -p $pluginPath
	echo '正在安装脚本文件...' > $install_tmp
	wget -O $pluginPath/ossfs_main.py $download_Url/ossfs/ossfs_main.py -T 5
	wget -O $pluginPath/index.html $download_Url/ossfs/index.html -T 5
	wget -O $pluginPath/info.json $download_Url/ossfs/info.json -T 5
	wget -O $pluginPath/icon.png $download_Url/ossfs/icon.png -T 5
	wget -O $pluginPath/ossfs   $download_Url/ossfs/ossfs -T 5
	\cp -a -r /www/server/panel/plugin/ossfs/ossfs  /etc/init.d/ossfs && chmod +x /etc/init.d/ossfs
	\cp -a -r /www/server/panel/plugin/ossfs/ossfs.png /www/server/panel/BTPanel/static/img/soft_ico/ico-ossfs.png
    if [ -f "/usr/bin/apt-get" ];then
    	update-rc.d ossfs defaults
    elif [ -f "/usr/bin/yum" ];then
    	chkconfig --add ossfs
    	chkconfig --level 2345 ossfs on
    fi
	echo '安装完成' > $install_tmp
}

Uninstall_ossfs()
{
	rm -rf $pluginPath
}

if [ "${1}" == 'install' ];then
	Install_ossfs
elif  [ "${1}" == 'update' ];then
	Uninstall_ossfs
elif [ "${1}" == 'uninstall' ];then
	Uninstall_ossfs
fi
