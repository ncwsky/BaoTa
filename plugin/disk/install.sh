#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

#配置插件下载地址和安装目录
download_url=http://download.bt.cn/disk
install_path=/www/server/panel/plugin/disk

#安装
Install()
{
	echo '正在安装...'
	#==================================================================
	#打包插件目录上传的情况下
	#依赖安装开始
	if [ -f "/usr/bin/yum" ]; then
    yum install -y e4fsprogs xfsprogs
	elif [ -f "/usr/bin/apt-get" ]; then
	apt-get install xfsprogs -y
	fi
	modprobe ext4
	modprobe xfs
	#依赖安装结束
	#==================================================================

	#==================================================================
	#使用命令行安装的情况下，如果使用面板导入的，请删除以下代码
	
	#创建插件目录
	mkdir -p $install_path

	#开始下载文件
	#文件下载结束
	cp -rf $install_path/icon.png "/www/server/panel/BTPanel/static/img/soft_ico/ico-disk.png"
	cp -rf $install_path/ing.gif "/www/server/panel/BTPanel/static/img/ing.gif"
	#==================================================================
	echo '================================================'
	echo '安装完成'
}

#卸载
Uninstall()
{
	rm -rf $install_path
}

#操作判断
if [ "${1}" == 'install' ];then
	Install
elif [ "${1}" == 'uninstall' ];then
	Uninstall
else
	echo 'Error!';
fi

##this is xf