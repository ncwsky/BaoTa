#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 日志同步到数据脚本
#	读取日志目录中所有站点的日志文件,将日志记录存入数据库中,并清空已转存的日志记录
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

#同步
def main():
	config_file = '/www/server/panel/plugin/liuliangtongji/config.json'
	#读取配置项
	if not os.path.exists(config_file):
		dblx="1"
		logpath='/www/wwwlogs/'
		diydbname='/www/server/panel/plugin/liuliangtongji/log.db'
	else:
		f_body = public.ReadFile(config_file)
		if not f_body:
			dblx="1"
			logpath='/www/wwwlogs/'
			diydbname='/www/server/panel/plugin/liuliangtongji/log.db'
		else:
			__config = json.loads(f_body)
			if not 'dblx' in __config:
				dblx="1"
			else:
				dblx=__config['dblx']
			if not 'logpath' in __config:
				logpath="/www/wwwlogs/"
			else:
				logpath=__config['logpath']
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
	dirlist = os.listdir(logpath) #列出文件夹下所有的目录与文件
	for i in range(0,len(dirlist)):
		if dirlist[i].find('log')>=0 and dirlist[i].find('error')<0 and dirlist[i] != 'access.log' and dirlist[i] != 'access_log':
			log_file = logpath+dirlist[i]
			websitecom=dirlist[i].replace('.log','')
			websitecom=websitecom.replace('-access_log','')
			totallogs=0
			with open(log_file, "r+") as f:
				contexts = f.readlines()
				log_timestr=''
				logarray=[]
				for line in contexts:   #读取每行日志
					totallogs=totallogs+1
					linearray=line.split()
					if len(linearray)>10:
						ip_attr = line.split()[0] #IP地址
						timestr=line.split()[3][1:-1].replace(":"," ",1) #将时间转换为17/Jun/2017 12:43:4格式
						log_timestr2=datetime.datetime.strptime(timestr,"%d/%b/%Y %H:%M:%S")  #将时间格式化为2017-06-17 12:43:04
						log_timestr=log_timestr2.strftime("%Y-%m-%d %H:%M:%S")
						httpmothed = line.split()[5].replace('"','')    #提交请求方式
						pageurl = cgi.escape(line.split()[6]) #访问页面
						httpstatus=line.split()[8] #状态码
						size = line.split()[9]  #流量大小
						shebieinfo=''
						if len(linearray)>10:
							for sbi in range(11,len(linearray)):
								shebieinfo=shebieinfo+" "+cgi.escape(line.split()[sbi])
						shebieinfo=shebieinfo.replace('"','')
						shebieinfo=shebieinfo.replace(' ','')
						pageurl=htmlencode(pageurl)
						shebieinfo=htmlencode(shebieinfo)
						httpmothed=htmlencode(httpmothed)
						websitecom=htmlencode(websitecom)
						ip_attr=htmlencode(ip_attr)
						log_timestr=htmlencode(log_timestr)
						size=htmlencode(size)
						httpstatus=htmlencode(httpstatus)
						datasql = "insert into weblogs(website,ip,time,httpstatus,size,httpmothed,pageurl,shebieinfo) values('%s', '%s','%s', '%s', '%s', '%s', '%s', '%s')" %(websitecom,ip_attr,log_timestr, httpstatus,size,httpmothed,pageurl,shebieinfo)
						conn.execute(datasql)
						#print datasql
				f.seek(0)
				f.truncate()
			print (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")+' '+websitecom+' 共同步 '+ str(totallogs) +' 条日志到数据库'
	log_conn.commit()
	conn.close()
	log_conn.close()

#过虑特殊字符
def htmlencode(strtxt):
	strtxt = strtxt.replace('?','&#63;')
	strtxt=strtxt.replace('"','')
	strtxt=strtxt.replace("'","");
	strtxt=strtxt.replace("\\", "");
	strtxt=strtxt.replace("(",'')
	strtxt=strtxt.replace(")",'')
	strtxt=strtxt.replace('+','')
	strtxt=strtxt.replace('>','')
	strtxt=strtxt.replace('<','')
	strtxt=strtxt.replace('*',"")
	strtxt=strtxt.replace('[','/[')
	strtxt=strtxt.replace(']','/]')
	strtxt=strtxt.replace('$','')
	return strtxt
if __name__ == "__main__":
    main()