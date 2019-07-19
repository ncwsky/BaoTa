#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 定期清理数据库日志记录脚本
#	自动清理设定天数以前的日志记录
# +-------------------------------------------------------------------
# | Copyright (c) 2019-2099 软程科技(https://rcwap.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 软程科技 石范
# +-------------------------------------------------------------------

import sys,os,json,hashlib,datetime,calendar,cgi,time,sqlite3
#设置运行目录
os.chdir("/www/server/panel")
#添加包引用位置并引用公共包
sys.path.append("class/")
import public

#清除
def main():
	config_file = '/www/server/panel/plugin/liuliangtongji/config.json'
    #读取配置项
	if not os.path.exists(config_file):
		dblx="1"
		dellogdays=90
		diydbname='/www/server/panel/plugin/liuliangtongji/log.db'
	else:
		f_body = public.ReadFile(config_file)
		if not f_body:
			dblx="1"
			dellogdays=90
			diydbname='/www/server/panel/plugin/liuliangtongji/log.db'
		else:
			__config = json.loads(f_body)
			if not 'dblx' in __config:
				dblx="1"
			else:
				dblx=__config['dblx']
			if not 'dellogdays' in __config:
				dellogdays=90
			else:
				dellogdays=int(__config['dellogdays'])
			if not 'diydbname' in __config:
				diydbname='/www/server/panel/plugin/liuliangtongji/log.db'
			else:
				diydbname=__config['diydbname']
	if dblx=="1":
		log_conn = sqlite3.connect('/www/server/panel/data/default.db')
	elif dblx=="2":
		log_conn = sqlite3.connect(diydbname)
	elif dblx=="3":
		import MySQLdb
		log_conn = MySQLdb.connect(__config['mysql_host'],__config['mysql_username'],__config['mysql_psd'],__config['mysql_db'], charset='utf8')
	conn = log_conn.cursor()
	startdate="2017-01-01 00:00:01"
	enddate=(datetime.datetime.now()-datetime.timedelta(days=dellogdays)).strftime("%Y-%m-%d 23:59:59")
	#public.M('weblogs').where('time>=? and time<=?',(startdate,enddate)).delete()
	conn.execute("delete from weblogs where time>='"+startdate+"' and time<='"+enddate+"'")
	log_conn.commit()
	conn.close()
	log_conn.close()
	print (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")+' 自动清理了 '+enddate+' 之前的日志记录'

if __name__ == "__main__":
    main()