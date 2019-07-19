#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 流量统计及日志分析
# +-------------------------------------------------------------------
# | Copyright (c) 2019-2099 软程科技(https://rcwap.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 石范
# +-------------------------------------------------------------------

import sys,os,json,hashlib,datetime,calendar,cgi,sqlite3
#设置运行目录
os.chdir("/www/server/panel")

#添加包引用位置并引用公共包
sys.path.append("class/")
import public,db,firewalls
#在非命令行模式下引用面板缓存和session对象
if __name__ != '__main__':
    from BTPanel import cache,session

class liuliangtongji_main:
    __plugin_path = "/www/server/panel/plugin/liuliangtongji/"
    __logspath = "/www/wwwlogs/"
    log_conn=""
    conn=""

    #构造方法
    def  __init__(self):
        self.logdb()
        pass

    #数据库连接
    def logdb(self):
         #读取配置项
        config_file = self.__plugin_path + 'config.json'
        dblx="1"  #数据库类型
        if not os.path.exists(config_file):
            dblx="1"
            diydbname=self.__plugin_path+'log.db'
        else:
            f_body = public.ReadFile(config_file)
            if not f_body:
                dblx="1"
                diydbname=self.__plugin_path+'log.db'
            else:
                __config = json.loads(f_body)
                if not 'dblx' in __config:
                    dblx="1"
                else:
                    dblx=__config['dblx']
                if not 'diydbname' in __config:
                    diydbname=self.__plugin_path+'log.db'
                else:
                    diydbname=__config['diydbname']
        if dblx=="1":
            self.log_conn = sqlite3.connect('/www/server/panel/data/default.db')
        elif dblx=="2":
            self.log_conn = sqlite3.connect(diydbname)
        elif dblx=="3":
            import MySQLdb
            self.log_conn = MySQLdb.connect(__config['mysql_host'],__config['mysql_username'],__config['mysql_psd'],__config['mysql_db'], charset='utf8')
        self.conn = self.log_conn.cursor()

    #检测mysqldb模块是否安装,如果未安装,则执行安装命令
    def isinstallmysqldb(self,args):
        try:
            import MySQLdb
            return {'status':1} 
        except:
            return {'status':0} 

    #判断mysql是否连接成功
    def mysqlisconnect(self,args):
        try:
            import MySQLdb
            MySQLdb.connect(args.mysql_host,args.mysql_username,args.mysql_psd,args.mysql_db, charset='utf8')
            return {'status':1} 
        except:
            return {'status':0} 

    #开启数据库模式
    def setdatabasemoshi(self,args):
        if not 'key' in args: args.key = 'moshi'
        if not 'value' in args: args.value = '1'
        self.set_config(args)
        exsql = '''create table weblogs (
            website text,
            ip VARCHAR(255),
            time DATETIME,
            httpstatus INT,
            size VARCHAR(255),
            httpmothed VARCHAR(255),
            pageurl text,
            shebieinfo text
            )'''
        #self.set_config({"key":'dblx',"value":'2'})
        res=self.conn.execute(exsql)
        return {'status':res}

    #获取站点列表
    def get_weblist(self,args):
        site_list = public.M('sites').field('id,name,ps').order('id desc').select()
        return {'weblist':site_list} 

    #清理数据库日志
    def del_logs(self,args):
        if not 'delstartdate' in args: args.delstartdate = (datetime.datetime.now()-datetime.timedelta(days=90)).strftime("%Y-%m-%d 00:00:01")
        if not 'delenddate' in args: args.delenddate = (datetime.datetime.now()-datetime.timedelta(days=90)).strftime("%Y-%m-%d 23:59:59")
        #public.M('weblogs').where('time>=? and time<=?',(args.delstartdate,args.delenddate)).delete()
        self.conn.execute("delete from weblogs where time>='"+args.delstartdate+"' and time<='"+args.delenddate+"'")
        self.log_conn.commit()
        return {'status':1}

    #将IP地址加入黑名单
    def iplahei(self,args):
        #os.system('iptables -I INPUT 1 -p tcp -s %s  -j DROP' % args.ip)
        fw=firewalls.firewalls()
        res=fw.AddDropAddress(args)
        return res

    #首页概况
    def get_index(self,args):
        #查询条件
        if not 'website' in args: args.website = 'access'
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        moshi=self.get_config(args)
        if not moshi or moshi['moshi'] != '1':
            #文件模式
            logdata=self.logsdata(args)
            ip = {}   # key为ip信息，value为ip数量（若重复则只增加数量）, size为流量信息
            iptem = []  # key为ip信息的临时组合
            totalsize = 0   #总流量
            totalvist = 0       #总访问量
            for line in logdata:   #读取每行日志
                ip_attr=line['ip']
                size=line['size']
                if size.isdigit():
                    sizenum=float(size)
                else:
                    sizenum=0
                if ip_attr in ip.keys():
                    temparray=ip[ip_attr]
                    temparray[0]=temparray[0]+1
                    temparray[1]=temparray[1]+sizenum
                    ip[ip_attr] = temparray
                else:
                    temparray=[1,sizenum]
                    ip[ip_attr] = temparray
                totalsize = totalsize+sizenum
                totalvist = totalvist+1
            sizestr=public.to_size(totalsize) 
            totalinfo=[totalvist,totalsize,len(ip),sizestr]
            #按访问量排序, 取前12名
            iparray=ip.keys()
            for index in range(len(ip)):
                iptxt=iparray[index]
                iptem.append([iptxt,ip[iptxt][0],ip[iptxt][1]])
            iplist=[]
            sizelist=[]
            iptem.sort(key=(lambda x:x[1]),reverse=True)
            for index in range(len(iptem)):
                if index < 12:
                    iplist.append([iptem[index][0],iptem[index][1]])
            iptem.sort(key=(lambda x:x[2]),reverse=True)
            for index in range(len(iptem)):
                if index < 12:
                    sizestr=public.to_size(iptem[index][2])
                    sizelist.append([iptem[index][0],sizestr])
        else:
            #数据库模式
            where="where website='"+args.website+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"'"
            #计算总流量与访问人次,
            self.conn.execute("select count(ip),sum(size),count(distinct ip) from weblogs "+where)
            totalinfo = self.conn.fetchone()
            totalsize=public.to_size(totalinfo[1])
            totalinfo=list(totalinfo)
            totalinfo.append(totalsize)
            #统计访问次数量多的前12位IP
            self.conn.execute("select ip,count(ip) AS count from weblogs "+where+" GROUP BY ip order by count desc limit 0,12")
            iplist = self.conn.fetchall()
            #统计流量最大的前12位IP
            self.conn.execute("select ip,sum(size) AS size from weblogs "+where+" GROUP BY ip order by size desc limit 0,12")
            sizelist = self.conn.fetchall()
            for index in range(len(sizelist)):
                line=list(sizelist[index])
                sizestr=public.to_size(line[1])
                line[1]=str(sizestr)
                sizelist=list(sizelist)
                sizelist[index]=line
        return {'totalinfo':totalinfo,'iplist':iplist,'sizelist':sizelist}

    #判断是否为有效的json
    def is_json(self,myjson):
        try:
            json.loads(myjson)
        except ValueError:
            return False
        return True

    #查询是否黑名单
    def isheimingdan(self,args):
        if public.M('firewall').where("port=?",(args.ip,)).count() > 0: 
            return {'stauts':1}
        else:
            return {'stauts':0}

    #流量图表数据
    def get_echarts(self,args):
        #根据传过来的参数,如果间距只有1天,则图表以小时为单位,否则以天为单位
        if not 'website' in args: args.website = 'access'
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        str_s_datetime = args.s_datetime
        str_e_datetime = args.e_datetime
        e_datetime=datetime.datetime.strptime(str_e_datetime,"%Y-%m-%d %H:%M:%S")
        s_datetime=datetime.datetime.strptime(str_s_datetime,"%Y-%m-%d %H:%M:%S")
        qujiandaysnum=(e_datetime-s_datetime).days  #查询日期区间天数
        x_zuobiao=[]    #x坐标
        fwdata=[]
        lldata=[]
        moshi=self.get_config(args)
        if not moshi or moshi['moshi'] != '1':
            logdata=self.logsdata(args)
        if qujiandaysnum > 1: #大于1天,则以天为单位
            for cxdays in range(0,qujiandaysnum):
                x_str=(s_datetime+datetime.timedelta(days=cxdays)).strftime("%Y-%m-%d")
                x_zuobiao.append(x_str) #x坐标
                x_s_time=x_str+" 00:00:01"
                x_e_time=x_str+" 23:59:59"
                totallldata=0
                totalfwdata=0
                if not moshi or moshi['moshi'] != '1':
                    for line in logdata:
                        log_timestr=line['time']
                        size=line['size']
                        if size.isdigit():
                            sizenum=float(size)
                        else:
                            sizenum=0
                        if log_timestr >= x_s_time and log_timestr <= x_e_time:
                            totallldata = totallldata+sizenum
                            totalfwdata=totalfwdata+1
                    lldata.append(round(totallldata/1024/1024,2))
                    fwdata.append(totalfwdata)
                else:
                    self.conn.close();
                    self.conn = self.log_conn.cursor()
                    wheretxt="where website='"+args.website+"' and time>='"+x_s_time+"' and time<='"+x_e_time+"'"
                    self.conn.execute("select count(ip) as totalip,sum(size) as totalsize from weblogs "+wheretxt)
                    logtotalinfo = self.conn.fetchone()
                    if not logtotalinfo[1]:
                        logtotalsize=0
                    else:
                        logtotalsize=logtotalinfo[1]
                    lldata.append(round(logtotalsize/1024/1024,2))
                    fwdata.append(logtotalinfo[0]) 
        else:   #小于1天,则以小时为单位
            for cxhours in range(0,24):
                cxhourstr = str(cxhours).zfill(2)
                x_zuobiao.append(cxhourstr) #x坐标
                x_s_time=str_s_datetime.split()[0]+" "+cxhourstr+":00:01"
                x_e_time=str_s_datetime.split()[0]+" "+cxhourstr+":59:59"
                totallldata=0
                totalfwdata=0
                if not moshi or moshi['moshi'] != '1':
                    for line in logdata:
                        log_timestr=line['time']
                        size=line['size']
                        if size.isdigit():
                            sizenum=float(size)
                        else:
                            sizenum=0
                        if log_timestr >= x_s_time and log_timestr <= x_e_time:
                            totallldata = totallldata+sizenum
                            totalfwdata=totalfwdata+1
                    lldata.append(round(totallldata/1024/1024,2))
                    fwdata.append(totalfwdata)
                else:
                    self.conn.close();
                    self.conn = self.log_conn.cursor()
                    wheretxt="where website='"+args.website+"' and time>='"+x_s_time+"' and time<='"+x_e_time+"'"
                    self.conn.execute("select count(ip) as totalip,sum(size) as totalsize from weblogs "+wheretxt)
                    logtotalinfo = self.conn.fetchone()
                    if not logtotalinfo[1]:
                        logtotalsize=0
                    else:
                        logtotalsize=logtotalinfo[1]
                    lldata.append(round(logtotalsize/1024/1024,2))
                    fwdata.append(logtotalinfo[0])
        return {'x_zuobiao':x_zuobiao,'fwdata':fwdata,'lldata':lldata}

    #获取所有站点排名
    def get_paiming(self,args):
        #根据传过来的参数,如果间距只有1天,则图表以小时为单位,否则以天为单位
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        str_s_datetime = args.s_datetime
        str_e_datetime = args.e_datetime
        e_datetime=datetime.datetime.strptime(str_e_datetime,"%Y-%m-%d %H:%M:%S")
        s_datetime=datetime.datetime.strptime(str_s_datetime,"%Y-%m-%d %H:%M:%S")
        qujiandaysnum=(e_datetime-s_datetime).days  #查询日期区间天数
        y_zuobiao=[]    #y坐标
        fwdata=[]
        lldata=[]
        #取站点列表
        sql = db.Sql()
        site_list = public.M('sites').field('id,name,ps').order('id desc').select()
        #self.conn.execute("select website,ip,CAST(time AS CHAR) AS time,httpstatus,size,httpmothed,pageurl,shebieinfo from weblogs where time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"' order by time desc")
        #logdata = self.conn.fetchall()
        for si in range(0,len(site_list)):
            y_zuobiao.append(site_list[si]['name'])
            #计算出这个时间段内这个站点的流量及访问量
            self.conn.close();
            self.conn = self.log_conn.cursor()
            wheretxt="where website='"+site_list[si]['name']+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"'"
            self.conn.execute("select count(ip) as totalip,sum(size) as totalsize from weblogs "+wheretxt)
            logtotalinfo = self.conn.fetchone()
            if not logtotalinfo[1]:
                logtotalsize=0
            else:
                logtotalsize=logtotalinfo[1]
            fwdata.append(logtotalinfo[0])
            lldata.append(round(logtotalsize/1024/1024,2))
        return {'y_zuobiao':y_zuobiao,'fwdata':fwdata,'lldata':lldata}

    #全站流量趋势
    def get_quanzhanqushi(self,args):
        #根据传过来的参数,如果间距只有1天,则图表以小时为单位,否则以天为单位
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        str_s_datetime = args.s_datetime
        str_e_datetime = args.e_datetime
        e_datetime=datetime.datetime.strptime(str_e_datetime,"%Y-%m-%d %H:%M:%S")
        s_datetime=datetime.datetime.strptime(str_s_datetime,"%Y-%m-%d %H:%M:%S")
        qujiandaysnum=(e_datetime-s_datetime).days  #查询日期区间天数
        x_zuobiao=[]    #x坐标
        fwdata=[]
        lldata=[]
        if qujiandaysnum > 1: #大于1天,则以天为单位
            for cxdays in range(0,qujiandaysnum):
                x_str=(s_datetime+datetime.timedelta(days=cxdays)).strftime("%Y-%m-%d")
                x_zuobiao.append(x_str) #x坐标
                x_s_time=x_str+" 00:00:01"
                x_e_time=x_str+" 23:59:59"
                self.conn.close();
                self.conn = self.log_conn.cursor()
                wheretxt="where time>='"+x_s_time+"' and time<='"+x_e_time+"'"
                self.conn.execute("select count(ip) as totalip,sum(size) as totalsize from weblogs "+wheretxt)
                logtotalinfo = self.conn.fetchone()
                if not logtotalinfo[1]:
                    logtotalsize=0
                else:
                    logtotalsize=logtotalinfo[1]
                lldata.append(round(logtotalsize/1024/1024,2))
                fwdata.append(logtotalinfo[0])
        else:   #小于1天,则以小时为单位
            for cxhours in range(0,24):
                cxhourstr = str(cxhours).zfill(2)
                x_zuobiao.append(cxhourstr) #x坐标
                x_s_time=str_s_datetime.split()[0]+" "+cxhourstr+":00:01"
                x_e_time=str_s_datetime.split()[0]+" "+cxhourstr+":59:59"
                self.conn.close();
                self.conn = self.log_conn.cursor()
                wheretxt="where time>='"+x_s_time+"' and time<='"+x_e_time+"'"
                self.conn.execute("select count(ip) as totalip,sum(size) as totalsize from weblogs "+wheretxt)
                logtotalinfo = self.conn.fetchone()
                if not logtotalinfo[1]:
                    logtotalsize=0
                else:
                    logtotalsize=logtotalinfo[1]
                lldata.append(round(logtotalsize/1024/1024,2))
                fwdata.append(logtotalinfo[0])
        return {'x_zuobiao':x_zuobiao,'fwdata':fwdata,'lldata':lldata}

    #分析日志中的IP统计
    def get_ipata(self,args):
        #查询条件
        if not 'website' in args: args.website = 'access'
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        if not 'orderby' in args: args.orderby = "count"
        if not 'p' in args: args.p = "1"
        moshi=self.get_config(args)
        if not moshi or moshi['moshi'] != '1':
            logdata=self.logsdata(args)
            ip = {}   # key为ip信息，value为ip数量（若重复则只增加数量）, size为流量信息
            iplist = []  # key为ip信息的临时组合
            for line in logdata:   #读取每行日志
                ip_attr=line['ip']
                size=line['size']
                if size.isdigit():
                    sizenum=float(size)
                else:
                    sizenum=0
                if ip_attr in ip.keys():
                    temparray=ip[ip_attr]
                    temparray[0]=temparray[0]+1
                    temparray[1]=temparray[1]+sizenum
                    temparray[2]=line['time']
                    temparray[3]=line['httpmothed']
                    temparray[4]=line['pageurl']
                    temparray[5]=line['shebieinfo']
                    temparray[6]=line['httpstatus']
                    ip[ip_attr] = temparray
                else:
                    temparray=[1,sizenum,line['time'],line['httpmothed'],line['pageurl'],line['shebieinfo'],line['httpstatus']]
                    ip[ip_attr] = temparray
            iparray=ip.keys()
            for index in range(len(ip)):
                iptxt=iparray[index]
                iplist.append([iptxt,ip[iptxt][0],ip[iptxt][1],args.website,iptxt,ip[iptxt][2],ip[iptxt][6],ip[iptxt][1],ip[iptxt][3],ip[iptxt][4],ip[iptxt][5]])
            if args.orderby=='count':
                iplist.sort(key=(lambda x:x[1]),reverse=True)
            else:
                iplist.sort(key=(lambda x:x[2]),reverse=True)
            page_data={"page":''}
        else:
            wheretxt="where website='"+args.website+"' and `time`>='"+args.s_datetime+"' and `time`<='"+args.e_datetime+"'"
            pagesize=(int(args.p)-1)*100
            self.conn.execute("select ip,count(ip) as totalcount,sum(size) AS totalsize,website,ip,CAST(time AS CHAR) AS time,httpstatus,size,httpmothed,pageurl,shebieinfo from weblogs "+wheretxt+" GROUP BY ip order by total"+args.orderby+" desc limit "+str(pagesize)+",100")
            iplist = self.conn.fetchall()
            #总数量
            self.conn.execute("select count(distinct(ip)) from weblogs "+wheretxt+" order by time desc")
            totallogs = self.conn.fetchone()[0] #总行数
            page_data = public.get_page(totallogs,int(args.p),100,'',result='1,2,3,4,5,6,7,8')
        return {"page":page_data,"data":iplist}

    #分析日志中的访问页面统计
    def get_urlata(self,args):
        #查询条件
        if not 'website' in args: args.website = 'access'
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        if not 'orderby' in args: args.orderby = "count"
        if not 'p' in args: args.p = "1"
        moshi=self.get_config(args)
        if not moshi or moshi['moshi'] != '1':
            logdata=self.logsdata(args)
            urlmd5 = {}   # key为ip信息，value为ip数量（若重复则只增加数量）, size为流量信息
            iplist = []  # key为ip信息的临时组合
            for line in logdata:   #读取每行日志
                pageurl=line['pageurl'].replace(' ', '')
                url_m = hashlib.md5()
                url_m.update(pageurl)
                pageurl_md5 = url_m.hexdigest() #访问页面的MD5值,此值将作为key
                size=line['size']
                if size.isdigit():
                    sizenum=float(size)
                else:
                    sizenum=0
                if pageurl_md5 in urlmd5.keys():
                    temparray=urlmd5[pageurl_md5]
                    temparray[0]=temparray[0]+1
                    temparray[1]=temparray[1]+sizenum
                    temparray[2]=line['time']
                    temparray[3]=line['httpmothed']
                    temparray[4]=line['pageurl']
                    temparray[5]=line['shebieinfo']
                    temparray[6]=line['httpstatus']
                    temparray[7]=line['ip']
                    urlmd5[pageurl_md5] = temparray
                else:
                    temparray=[1,sizenum,line['time'],line['httpmothed'],line['pageurl'],line['shebieinfo'],line['httpstatus'],line['ip']]
                    urlmd5[pageurl_md5] = temparray
            iparray=urlmd5.keys()
            for index in range(len(urlmd5)):
                iptxt=iparray[index]
                iplist.append([urlmd5[iptxt][4],urlmd5[iptxt][0],urlmd5[iptxt][1],args.website,urlmd5[iptxt][7],urlmd5[iptxt][2],urlmd5[iptxt][6],urlmd5[iptxt][1],urlmd5[iptxt][3],urlmd5[iptxt][4],urlmd5[iptxt][5]])
            if args.orderby=='count':
                iplist.sort(key=(lambda x:x[1]),reverse=True)
            else:
                iplist.sort(key=(lambda x:x[2]),reverse=True)
            page_data={"page":''}
        else:
            where="where website='"+args.website+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"'"
            pagesize=(int(args.p)-1)*100
            self.conn.execute("select pageurl,count(*) AS count,sum(size) AS size,website,ip,CAST(time AS CHAR) AS time,httpstatus,size,httpmothed,pageurl,shebieinfo from weblogs "+where+" GROUP BY pageurl order by "+args.orderby+" desc limit "+str(pagesize)+",100")
            iplist = self.conn.fetchall()
            #总数量
            self.conn.execute("select count(distinct(pageurl)) from weblogs "+where+" order by time desc")
            totallogs = self.conn.fetchone()[0] #总行数
            page_data = public.get_page(totallogs,int(args.p),100,'',result='1,2,3,4,5,6,7,8')
        return {"page":page_data,"data":iplist}

    #读取原始日志记录
    def get_oldloglist(self,args):
        #查询条件
        if not 'website' in args: args.website = 'access'
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        if not 'sxlx' in args: args.sxlx = ''
        if not 'keyword' in args: args.keyword = ''
        if not 'p' in args: args.p = "1"
        moshi=self.get_config(args)
        if not moshi or moshi['moshi'] != '1':
            logdata=self.logsdata(args)
            iplist=[]
            for line in logdata:   #读取每行日志
                iplist.append([args.website,line['ip'],line['time'],line['httpstatus'],line['size'],line['httpmothed'],line['pageurl'],line['shebieinfo']])
            page_data={"page":''}
        else:
            if not (args.sxlx).strip() or not (args.keyword).strip():
                where="where website='"+args.website+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"'"
            elif args.sxlx=='ip':
                where="where website='"+args.website+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"' and ip like '%"+args.keyword+"%'"
            elif args.sxlx=='url':
                where="where website='"+args.website+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"' and pageurl like '%"+args.keyword+"%'"
            elif args.sxlx=='status':
                where="where website='"+args.website+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"' and httpstatus like '%"+args.keyword+"%'"
            elif args.sxlx=='shebei':
                where="where website='"+args.website+"' and time>='"+args.s_datetime+"' and time<='"+args.e_datetime+"' and shebieinfo like '%"+args.keyword+"%'"
            pagesize=(int(args.p)-1)*100
            self.conn.execute("select website,ip,CAST(time AS CHAR) AS time,httpstatus,size,httpmothed,pageurl,shebieinfo from weblogs "+where+" order by time desc limit "+str(pagesize)+",100")
            iplist = self.conn.fetchall()
            #总数量
            self.conn.execute("select count(ip) from weblogs "+where+" order by time desc")
            totallogs = self.conn.fetchone()[0] #总行数
            page_data = public.get_page(totallogs,int(args.p),100,'',result='1,2,3,4,5,6,7,8')
        return {"page":page_data,"data":iplist}

    #读取配置文件
    def get_config(self,args):
        #判断是否从文件读取配置
        config_file = self.__plugin_path + 'config.json'
        if not os.path.exists(config_file): return None
        f_body = public.ReadFile(config_file)
        if not f_body: return None
        self.__config = json.loads(f_body)
        return self.__config

    #写配置文件
    def set_config(self,args):
        __config=self.get_config('')
        #是否需要初始化配置项
        if not __config: __config = {}
        #是否需要设置配置值
        if args.key:
            __config[args.key] = args.value
        #写入到配置文件
        config_file = self.__plugin_path + 'config.json'
        public.WriteFile(config_file,json.dumps(__config))
        return True

    #查找文件,根据站点名查找
    def searchfile(self,args):
        if not 'website' in args: args.website = 'access'
        config=self.get_config(args)
        if not config:
            logpath=self.__logspath
        else:
            if not 'logpath' in config: 
                logpath=self.__logspath
            else:
                logpath=config['logpath']
        dirlist = os.listdir(logpath)
        result=''
        for i in range(0,len(dirlist)):
            if dirlist[i].startswith(args.website) and dirlist[i].find('error')<0:
                result=dirlist[i]
        return {'filename':logpath+result}

    #读取日志文件内容
    def logsdata(self,args):
        if not 'website' in args: args.website = 'access'
        if not 's_datetime' in args: args.s_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 00:00:01")
        if not 'e_datetime' in args: args.e_datetime = (datetime.datetime.now()).strftime("%Y-%m-%d 23:59:59")
        if not 'sxlx' in args: args.sxlx = ''
        if not 'keyword' in args: args.keyword = ''
        if not 'page' in args: args.page = 0
        #读取日志路径
        log_file_json=self.searchfile(args)
        log_file = log_file_json['filename']
        with open(log_file) as f:
            contexts = f.readlines()
            log_timestr=''
            logarray=[]
            for line in contexts:   #读取每行日志
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
                    if log_timestr >= args.s_datetime and log_timestr <= args.e_datetime:
                        #判断筛选条件
                        if not (args.sxlx).strip() or not (args.keyword).strip():
                            logtxt={'ip':ip_attr,'time':log_timestr,'httpmothed':httpmothed,'pageurl':pageurl,'httpstatus':httpstatus,'size':size,'shebieinfo':shebieinfo}
                            logarray.append(logtxt)
                        elif args.sxlx=='ip':
                            if ip_attr.find(args.keyword)>=0 :
                                logtxt={'ip':ip_attr,'time':log_timestr,'httpmothed':httpmothed,'pageurl':pageurl,'httpstatus':httpstatus,'size':size,'shebieinfo':shebieinfo}
                                logarray.append(logtxt)
                        elif args.sxlx=='url':
                            if pageurl.find(args.keyword)>=0 :
                                logtxt={'ip':ip_attr,'time':log_timestr,'httpmothed':httpmothed,'pageurl':pageurl,'httpstatus':httpstatus,'size':size,'shebieinfo':shebieinfo}
                                logarray.append(logtxt)
                        elif args.sxlx=='status':
                            if httpstatus.find(args.keyword)>=0 :
                                logtxt={'ip':ip_attr,'time':log_timestr,'httpmothed':httpmothed,'pageurl':pageurl,'httpstatus':httpstatus,'size':size,'shebieinfo':shebieinfo}
                                logarray.append(logtxt)
                        elif args.sxlx=='shebei':
                            if shebieinfo.find(args.keyword)>=0 :
                                logtxt={'ip':ip_attr,'time':log_timestr,'httpmothed':httpmothed,'pageurl':pageurl,'httpstatus':httpstatus,'size':size,'shebieinfo':shebieinfo}
                                logarray.append(logtxt)
        return logarray