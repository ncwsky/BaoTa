#!/usr/bin/python
# coding: utf-8
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import time,hashlib,sys,os,json,requests,re,public,random,string
sys.setrecursionlimit(50000)
class psync_api_main:
    __BT_KEY = ''
    __BT_PANEL = ''
    __vhost='/www/server/panel/vhost/'
    __data='/www/server/panel/data/'
    __nginx_config='/www/server/panel/vhost/nginx/'
    __apache_config='/www/server/panel/vhost/apache/'
    __wwwroot = '/www/wwwroot'
    logPath = '/www/server/panel/plugin/psync_api/api.log'
    pane_api = '/www/server/panel/plugin/psync_api/user.json'
    _request = None
    _site_info=None
    _chmoe = []
    _porxy=None
    _redirect=None
    _ftp_info=[]
    _Speed=None
    _start_config='/www/server/panel/plugin/psync_api/start_config.json'

    def __init__(self):
        self._site_info=self.get_site_info(None)
        self._request = requests.session()
        if not os.path.exists(self.logPath):
            ret={}
            public.writeFile(self.logPath, json.dumps(ret))

        if not os.path.exists(self.pane_api):
            ret = {}
            public.writeFile(self.pane_api, json.dumps(ret))
        if not os.path.exists(self._start_config):
            ret={}
            public.writeFile(self._start_config, json.dumps(ret))

       # 初始化面板信息
        get_panel=self.get_panel_api(None)
        if get_panel['status']:
            self.__BT_KEY=get_panel['msg']['api_token']
            self.__BT_PANEL=get_panel['msg']['panel']

    # 检测面板API 是否通信正常
    def chekc_panel_api(self):
        p_data=self.get_key_data()
        p_data['action']='GetSystemTotal'
        time.sleep(1)
        #return p_data
        #return json.loads(ret.text)
        try:
            ret = self._request.post(self.__BT_PANEL + '/system?action=GetSystemTotal', p_data)
            ret=json.loads(ret.text)
            if ret['system']:
                return True
            else:
                return False
        except:
            return False

    #添加面板的API
    def add_panel_api(self,get):
        if not 'panel' in get:return public.returnMsg(False, "请填写你的面板地址")
        if not 'api_token' in get: return public.returnMsg(False, "请填写你的面板的API")
        ret={}
        ret['panel']= get.panel
        ret['api_token']=get.api_token
        self.__BT_KEY=get.api_token
        self.__BT_PANEL=get.panel
        if not self.chekc_panel_api():
           return public.returnMsg(False, "添加失败。请查看是否当前IP加入到面板的API的白名单")
        public.writeFile(self.pane_api, json.dumps(ret))
        return public.returnMsg(True, '添加成功')


    #获取面板api_token
    def get_panel_api(self,get):
        if os.path.exists(self.pane_api):
            ret=json.loads(public.readFile(self.pane_api))
            if len(ret)==0:
                return public.returnMsg(False, {"panel":'',"api_token":''})
            else:
                return public.returnMsg(True,ret)

    #本机环境
    def CheckServer(self, get):
        serverInfo = {}
        serverInfo['status']=True
        serverInfo['webserver'] = 'apache'
        if os.path.exists('/www/server/nginx/sbin/nginx'): serverInfo['webserver'] = 'nginx'
        serverInfo['php'] = []
        phpversions = ['52', '53', '54', '55', '56', '70', '71','72','73']
        phpPath = '/www/server/php/'
        for pv in phpversions:
            if not os.path.exists(phpPath + pv + '/bin/php'): continue
            serverInfo['php'].append(pv)
        serverInfo['mysql'] = False
        if os.path.exists('/www/server/mysql/bin/mysql'): serverInfo['mysql'] = True
        serverInfo['ftp'] = False
        if os.path.exists('/www/server/pure-ftpd/bin/pure-pw'): serverInfo['ftp'] = True
        if os.path.exists('/www/server/panel/runserver.py'):
            serverInfo['version'] = 6
        else:
            serverInfo['version'] = 5
        import psutil
        try:
            diskInfo = psutil.disk_usage('/www')
        except:
            diskInfo = psutil.disk_usage('/')
        serverInfo['disk'] = diskInfo[2]
        return serverInfo

    # 检测面板API 是否通信正常
    def get_api_pane_server(self,get):
        p_data=self.get_key_data()
        #return p_data
        try:
            ret =self._request.post(self.__BT_PANEL + '/system?action=GetConcifInfo', p_data)
            disk=self._request.post(self.__BT_PANEL + '/system?action=GetDiskInfo', p_data)
        except:
            return False
        try:
            ret=json.loads(ret.text)
            disk=json.loads(disk.text)
            if ret['status']:
                result={}
                result['php'] = []
                if 'webserver' in ret:
                    result['webserver'] = ret['webserver']
                if 'mysql' in ret:
                    result['mysql']=ret['mysql']['status']
                if 'pure-ftpd' in ret:
                    result['ftp'] = ret['pure-ftpd']['status']
                if 'php' in ret:
                    for i in ret['php']:
                        result['php'].append(i['version'])
                result['status']=True
                result['version']=6
                result['disk']=disk
                return result
            else:
                return False
        except:
            return False

    #检测两方环境
    def chekc_surroundings(self,get):
        ret={}
        ret['local']=self.CheckServer(None)
        api_panel=self.get_api_pane_server(None)
        if not api_panel:
            return public.returnMsg(False, "获取不到对方机器的环境信息。请修复面板再尝试一下")
        ret['api_panel']=api_panel
        return ret

    # 查询日志(查看进度)
    def get_api_log(self,get):
        if not os.path.exists(self.logPath):public.returnMsg(False, "无日志")
        ret=json.loads(public.readFile(self.logPath))
        if int(len(ret))==0:
            return public.returnMsg(False, "无日志")
        return public.returnMsg(True,ret)

    #写输出日志
    def WriteLogs(self,logMsg):
        fp = open(self.logPath,'w+')
        fp.write(logMsg)
        fp.close()

    def get_key_data(self):
        now_time = int(time.time())
        p_data = {
            'request_token': self.__get_md5(str(now_time) + '' + self.__get_md5(self.__BT_KEY)),
            'request_time': now_time
            #'k':self.__BT_KEY
        }
        return p_data

    # 查看所有站点信息
    def get_site_info(self,get):
        data = {}
        data['sites'] = public.M('sites').field('id,name,path,status,ps,addtime').select()
        data['databases'] = public.M('databases').field('name,username,password,accept,ps,addtime').select()
        data['ftps'] = public.M('ftps').field('pid,name,password,path,status,ps,addtime').select()
        data['binding']=public.M('binding').field('id,pid,path,port,domain').select()
        self._site_info=data
        if data['binding']:
            for i in data['binding']:
                for i2 in data['sites']:
                    if i2['id']==i['pid']:
                        if not 'er' in i2:
                            i2['er']=[]
                        i2['er'].append(i)
        return data



    # 调用消息队列
    def start_task(self,get):
        if not 'site' in get: return public.returnMsg(False, "请选择你需要的站点")
        if not 'database' in get: return public.returnMsg(False, "请选择你需要的数据库")
        if not 'ftps' in get: return public.returnMsg(False, "请选择你需要的ftp")
        ret={}
        ret['site']=json.loads(get.site)
        ret['database']=json.loads(get.database)
        ret['ftps']=json.loads(get.ftps)
        #写入配置文件
        public.writeFile(self._start_config, json.dumps(ret))
        #启动消息队列
        import panelTask
        t=panelTask.bt_task()
        t.create_task('一键迁移正在迁移中',0,'python /www/server/panel/plugin/psync_api/psync_api_main.py')
        return public.returnMsg(True, '正在迁移中')

    # 读取文件
    def get_config(self):
        ret=public.readFile(self._start_config)
        try:
           ret=json.loads(ret)
           return ret
        except:
            return False

    #开始迁移
    def start_transfer(self):
        # site=json.loads(get.site)
        # database=json.loads(get.database)
        # ftps=json.loads(get.ftps)
        os.system('rm -rf %s' % self.logPath)
        get_config=self.get_config()
        if not get_config:
            Speed = {}
            Speed['name'] = '获取迁移数据失败。请重试'  # 描述
            Speed['total'] = 0
            Speed['current'] = None  # 现在的类型
            Speed['count'] = 0  # 已经完成多少
            Speed['Current_file'] = None  # 当前发送的文件
            Speed['progress'] = 0  # 进度
            Speed['ok'] = True
            Speed['return_result'] = []
            Speed['status']=False
            self._Speed = Speed
            self.WriteLogs(json.dumps(self._Speed))
        else:
            site = get_config['site']
            database=get_config['database']
            ftps=get_config['ftps']
            resutl=[]
            # 进度
            Speed={}
            Speed['name']=None   # 描述
            Speed['total']=len(site)+len(database)+len(ftps) # 总数
            Speed['current']=None   #现在的类型
            Speed['count']=0         #已经完成多少
            Speed['Current_file']=None   # 当前发送的文件
            Speed['progress']=0          # 进度
            Speed['ok'] = False
            Speed['status'] = True
            Speed['return_result']=[]
            self._Speed=Speed
            self.WriteLogs(json.dumps(self._Speed))
            if len(site)>=1:
                for i in site:
                    ret=self.send_site(i)
                    data={}
                    data['name']=i
                    data['type'] = '网站'
                    data['resutl']=ret
                    if not self._Speed == None:
                        self._Speed['return_result'].append(data)
                        self.WriteLogs(json.dumps(self._Speed))
                    resutl.append(data)

            if len(database)>=1:
                for i in database:
                    ret = self.send_database(i)
                    data = {}
                    data['name'] = i
                    data['type']='数据库'
                    data['resutl'] = ret
                    if not self._Speed == None:
                        self._Speed['return_result'].append(data)
                        self.WriteLogs(json.dumps(self._Speed))
                    resutl.append(data)

            if len(ftps) >= 1:
                for i in ftps:
                    ret = self.send_ftps(i)
                    data = {}
                    data['name'] =i
                    data['type'] = 'FTP'
                    data['resutl'] = ret
                    if not self._Speed == None:
                        self._Speed['return_result'].append(data)
                        self.WriteLogs(json.dumps(self._Speed))
                    resutl.append(data)


            if not self._Speed == None:
                self._Speed['name'] = '迁移完成'
                self._Speed['ok']=True
                self.WriteLogs(json.dumps(self._Speed))
           # os.system('rm -rf %s'%self.logPath)
            os.system('rm -rf /www/wwwroot/*.sql')
            return resutl

    # 发送数据库
    def send_database(self, database,all=False):
        database_backup_path = self.BackupDatabase(database)
        if not self._Speed == None:
            self._Speed['name'] = '正在发送数据库%s' % database
            self._Speed['current'] = 'database'
            #self._Speed['count'] += 1
           # self._Speed['progress'] = "%.2f%%" % (float(self._Speed['count']) / float(self._Speed['total']) * 100)
            self._Speed['Current_file']=database
            self.WriteLogs(json.dumps(self._Speed))
        insert_data = self.insert_database(database)
        if insert_data:
            self.upload_file(self.__wwwroot, database_backup_path)
            ret = self.set_database_table(database, database_backup_path)
            self.del_database(database_backup_path)
            os.remove(database_backup_path)
            if not self._Speed == None:
                self._Speed['count'] += 1
                self._Speed['progress'] = "%.2f" % (float(self._Speed['count']) / float(self._Speed['total']) * 100)
                self._Speed['name'] = '成功发送数据库%s==>OK' % database
                self.WriteLogs(json.dumps(self._Speed))

            if not self._Speed == None:
                self._Speed['name'] = '数据库%s 已经成功迁移==>OK' % database
                self.WriteLogs(json.dumps(self._Speed))
            return ret['status']
        else:
            if not self._Speed == None:
                self._Speed['count'] += 1
                self._Speed['progress'] = "%.2f" % (float(self._Speed['count']) / float(self._Speed['total']) * 100)
                self.WriteLogs(json.dumps(self._Speed))
        return False

    #发送网站
    def send_site(self,site,all=False):
        if not self._site_info:self.get_site_info(None)
        for i in self._site_info['sites']:
            if i['name']==site:
                if not self._Speed==None:
                    self._Speed['name']='正在发送网站%s'%site
                    self._Speed['current'] = 'site'
                    #self._Speed['count'] +=1
                    #self._Speed['progress']="%.2f" % (float(self._Speed['count']) / float(self._Speed['total']) * 100)
                    self.WriteLogs(json.dumps(self._Speed))
                #存在二级目录
                if 'er' in i:
                    ret2=self.insert_site(site, i['path'])
                    if ret2:
                        self.upload_file(str(i['path']), str(i['path']))
                        self._redirect = self.get_redirect_config(None)
                        self._porxy = self.get_proxy_config(None)

                        if 'siteId' in ret2:
                            p_data = self.get_key_data()
                            p_data['id']=ret2['siteId']
                            for i2 in i['er']:
                                p_data['domain'] = i2['domain']
                                p_data['dirName']=i2['path']
                                ret = self._request.post(self.__BT_PANEL + '/site?action=AddDirBinding', data=p_data)
                        self.send_site_ssl(site)
                        self.send_proxy_redirect()
                        if not self._Speed == None:
                            self._Speed['count'] += 1
                            self._Speed['progress'] = "%.2f" % (
                                        float(self._Speed['count']) / float(self._Speed['total']) * 100)
                            self.WriteLogs(json.dumps(self._Speed))

                        return True
                    else:
                        if not self._Speed == None:
                            self._Speed['count'] += 1
                            self._Speed['progress'] = "%.2f" % (
                                        float(self._Speed['count']) / float(self._Speed['total']) * 100)
                            self.WriteLogs(json.dumps(self._Speed))
                        return False

                # 不存在二级目录
                else:
                    if self.insert_site(site,i['path']):
                        self.upload_file(str(i['path']), str(i['path']))
                        self._redirect = self.get_redirect_config(None)
                        self._porxy = self.get_proxy_config(None)
                        self.send_site_ssl(site)
                        self.send_proxy_redirect()
                        if not self._Speed == None:
                            self._Speed['count'] += 1
                            self._Speed['progress']="%.2f" % (float(self._Speed['count']) / float(self._Speed['total']) * 100)
                            self.WriteLogs(json.dumps(self._Speed))
                        return True
                    else:
                        if not self._Speed == None:
                            self._Speed['count'] += 1
                            self._Speed['progress'] = "%.2f" % (
                                        float(self._Speed['count']) / float(self._Speed['total']) * 100)
                            self.WriteLogs(json.dumps(self._Speed))
                        return False
        return False

    # 发送ftps
    def send_ftps(self,ftp,all=False):
        if all:
            error = '''"status": false'''
            data = self.get_key_data()
            for i in self._site_info['ftps']:
                if not self._Speed == None:
                    self._Speed['name'] = '正在建立ftp用户%s' % i['name']
                    self._Speed['current'] = 'ftps'
                    self._Speed['count'] += 1
                    self._Speed['progress'] = "%.2f" % (float(self._Speed['count']) / float(self._Speed['total']) * 100)
                    self._Speed['Current_file'] = i['name']
                    self.WriteLogs(json.dumps(self._Speed))
                data['ftp_username'] = i['name']
                data['ftp_password'] = i['password']
                data['path'] = i['path']
                data['ps'] = i['ps']
                ret = self._request.post(self.__BT_PANEL + '/ftp?action=AddUser', data=data)
                if error in ret.text: status = False
                if not self._Speed == None:
                    self._Speed['name'] = '成功建立ftp用户%s===>OK' % i['name']
                    self.WriteLogs(json.dumps(self._Speed))
                try:
                    status = json.loads(ret.text)
                    status = status['status']
                except:
                    status = False
                ftp_info = {}
                ftp_info['user'] = i['name']
                ftp_info['status'] = status
                self._ftp_info.append(ftp_info)
        else:
            error = '''"status": false'''
            data = self.get_key_data()
            for i in self._site_info['ftps']:
                if i['name']==ftp:
                    if not self._Speed == None:
                        self._Speed['name'] = '正在建立ftp用户%s' % i['name']
                        self._Speed['current'] = 'ftps'
                        self._Speed['count'] += 1
                        self._Speed['progress'] = "%.2f" % (float(self._Speed['count']) / float(self._Speed['total']) * 100)
                        self._Speed['Current_file'] = i['name']
                        self.WriteLogs(json.dumps(self._Speed))
                    data['ftp_username']=i['name']
                    data['ftp_password']=i['password']
                    data['path']=i['path']
                    data['ps']=i['ps']
                    ret=self._request.post(self.__BT_PANEL + '/ftp?action=AddUser', data=data)
                    if error in ret.text: status=False
                    try:
                        status=json.loads(ret.text)
                        status=status['status']
                    except:
                        status=False

                    ftp_info={}
                    ftp_info['user']=i['name']
                    ftp_info['status']=status
                    self._ftp_info.append(ftp_info)
                    return status
        return False

    # 新建网站
    def insert_site(self, site,path):
        p_data=self.get_key_data()
        ret = {"domain": site, "domainlist": [], "count": 0}
        p_data['webname'] = json.dumps(ret)
        p_data['port'] = "80"
        p_data['ftp'] = 'false'
        p_data['sql'] = 'false'
        p_data['version'] = '00'
        p_data['ps'] = site
        p_data['path'] = path
        ret =self._request.post(self.__BT_PANEL + '/site?action=AddSite', data=p_data)
        if 'status' in ret.text: return False
        try:
            return json.loads(ret.text)
        except:
            return False


    #打包网站配置文件
    def send_site_ssl(self,site):
        #网站证书
        if os.path.exists(self.__vhost+'cert/'+site):
            if not self._Speed == None:
                self._Speed['Current_file'] = '正在发送%s网站的SSL证书'%site
                self.WriteLogs(json.dumps(self._Speed))
            self.upload_file(self.__vhost+'cert/'+site,self.__vhost+'cert/'+site)
            if not self._Speed == None:
                self._Speed['Current_file'] = '已经成功发送%s网站的SSL证书===>OK'%site
                self.WriteLogs(json.dumps(self._Speed))

        if os.path.exists('/etc/letsencrypt/live/'+site):
            self.upload_file('/etc/letsencrypt/live/'+site,'/etc/letsencrypt/live/'+site)

        #发送反代文件
        if os.path.exists(self.__vhost+'nginx/proxy/'+site):
            if not self._Speed == None:
                self._Speed['Current_file'] = '正在发送%s网站Nginx的反代文件'%site
                self.WriteLogs(json.dumps(self._Speed))
            self.upload_file(self.__vhost+'nginx/proxy/'+site, self.__vhost+'nginx/proxy/'+site)
            if not self._Speed == None:
                self._Speed['Current_file'] = '成功发送%s网站Nginx的反代文件==>OK'%site
                self.WriteLogs(json.dumps(self._Speed))


        if os.path.exists(self.__vhost+'apache/proxy/'+site):
            if not self._Speed == None:
                self._Speed['Current_file'] = '正在发送%s网站Apache的反代文件' % site
                self.WriteLogs(json.dumps(self._Speed))
            self.upload_file(self.__vhost+'apache/proxy/'+site, self.__vhost+'apache/proxy/'+site)
            if not self._Speed == None:
                self._Speed['Current_file'] = '成功发送%s网站Apache的反代文件==>OK' % site
                self.WriteLogs(json.dumps(self._Speed))

        #发送反代文件
        if os.path.exists(self.__vhost+'nginx/redirect/'+site):
            self.upload_file(self.__vhost+'nginx/redirect/'+site,self.__vhost+'nginx/redirect/'+site)
        if os.path.exists(self.__vhost+'apache/redirect/'+site):
            self.upload_file(self.__vhost+'apache/redirect/'+site,self.__vhost+'apache/redirect/'+site)

        self.redirect(site)
        self.proxy(site)

        #伪静态
        if os.path.exists('/www/server/panel/vhost/rewrite/'+site+'.conf'):
            if not self._Speed == None:
                self._Speed['Current_file'] = '正在发送%s网站的伪静态文件' % site
                self.WriteLogs(json.dumps(self._Speed))
            self.upload_file('/www/server/panel/vhost/rewrite/','/www/server/panel/vhost/rewrite/'+site+'.conf')
            if not self._Speed == None:
                self._Speed['Current_file'] = '成功发送%s网站的伪静态文件==>OK' % site
                self.WriteLogs(json.dumps(self._Speed))

        # 二级目录伪静态
        for w_san in os.listdir('/www/server/panel/vhost/rewrite/'):
            if w_san.find(site+'_') != -1:
                if not self._Speed == None:
                    self._Speed['Current_file'] = '正在发送%s网站的二级目录伪静态文件' % site
                    self.WriteLogs(json.dumps(self._Speed))
                self.upload_file('/www/server/panel/vhost/rewrite/','/www/server/panel/vhost/rewrite/'+w_san)
                if not self._Speed == None:
                    self._Speed['Current_file'] = '成功发送%s网站的二级目录伪静态文件==>OK' % site
                    self.WriteLogs(json.dumps(self._Speed))
        #发送配置文件
        if os.path.exists(self.__vhost+'nginx/'+site+'.conf'):
            if not self._Speed == None:
                self._Speed['Current_file'] = '正在发送%s网站的Nginx配置文件' % site
                self.WriteLogs(json.dumps(self._Speed))
            self.upload_file(self.__vhost+'nginx/', self.__vhost+'nginx/'+site+'.conf')
            if not self._Speed == None:
                self._Speed['Current_file'] = '成功发送%s网站的Nginx配置文件==>OK' % site
                self.WriteLogs(json.dumps(self._Speed))

        if os.path.exists(self.__vhost+'apache/'+site+'.conf'):
            if not self._Speed == None:
                self._Speed['Current_file'] = '正在发送%s网站的Apache配置文件' % site
                self.WriteLogs(json.dumps(self._Speed))
            self.upload_file(self.__vhost+'apache/', self.__vhost+'apache/'+site+'.conf')
            if not self._Speed == None:
                self._Speed['Current_file'] = '成功发送%s网站的Apache配置文件==>OK' % site
                self.WriteLogs(json.dumps(self._Speed))
        return True

    #发送proxy
    def send_proxy_redirect(self):
        if self._porxy:
            data = self.get_key_data()
            data['path'] = self.__data + 'proxyfile.json'
            data['encoding']='utf-8'
            data['data']=json.dumps(self._porxy)
            self._request.post(self.__BT_PANEL + '/files?action=SaveFileBody', data=data)
        if self._redirect:
            data = self.get_key_data()
            data['path'] = self.__data + 'redirect.conf'
            data['encoding']='utf-8'
            data['data']=json.dumps(self._redirect)
            self._request.post(self.__BT_PANEL + '/files?action=SaveFileBody', data=data)

    def redirect(self,site):
        if os.path.exists(self.__data + 'redirect.conf'):
            if not self._redirect: self._redirect=[]
            porxy_json = json.loads(public.readFile(self.__data + 'redirect.conf'))
            if len(porxy_json) == 0:
                pass
            else:
                if len(self._redirect)==0:
                    for i2 in porxy_json:
                        if i2['sitename'] == site:
                            self._redirect.append(i2)
                else:
                    if len(porxy_json) >= 1:
                        for i in self._redirect:
                            if i['sitename'] == site:
                                continue
                            else:
                                for i2 in porxy_json:
                                    if i2['sitename'] == site:
                                        self._redirect.append(i2)
            return True

    # 发送反代配置文件config
    def proxy(self,site):
        if os.path.exists(self.__data + 'proxyfile.json'):
            if not self._porxy: self._porxy=[]
            porxy_json = json.loads(public.readFile(self.__data + 'proxyfile.json'))
            if len(porxy_json) == 0:
                pass
            else:
                if len(self._porxy)==0:
                    for i2 in porxy_json:
                        if i2['sitename'] == site:
                            self._porxy.append(i2)
                else:
                    if len(porxy_json) >= 1:
                        for i in self._porxy:
                            if i['sitename'] == site:
                                continue
                            else:
                                for i2 in porxy_json:
                                    if i2['sitename'] == site:
                                        self._porxy.append(i2)
            return True

    #读取反代配置文件config
    def get_proxy_config(self,get):
        error='''"status": false'''
        data = self.get_key_data()
        data['path']=self.__data+'proxyfile.json'
        ret = self._request.post(self.__BT_PANEL + '/files?action=GetFileBody', data=data)
        if error in ret.text: return False
        ret=json.loads(ret.text)
        return json.loads(ret['data'])

    def get_redirect_config(self,get):
        error='''"status": false'''
        data = self.get_key_data()
        data['path']=self.__data+'redirect.conf'

        ret = self._request.post(self.__BT_PANEL + '/files?action=GetFileBody', data=data)
        if error in ret.text: return False
        ret=json.loads(ret.text)
        return json.loads(ret['data'])


    # 导出数据库
    def BackupDatabase(self, name):
        if not self._Speed == None:
            self._Speed['name'] = '正在打包数据库%s' % name
            self._Speed['current'] = 'database'
            self.WriteLogs(json.dumps(self._Speed))
        ret=public.M('config').field('mysql_root').select()
        username='root'
        password=ret[0]['mysql_root']
        backupPath = self.__wwwroot
        if not os.path.exists(backupPath):
            os.system('mkdir -p ' + backupPath)
            os.system('chmod -R 600 ' + backupPath)
        backupName = backupPath + '/db_' + name + '_' + str(time.time()) + '.sql'
        public.ExecShell(
            "/www/server/mysql/bin/mysqldump -u" + username + " -p" + password + " " + name +'>' +backupName)
        if not os.path.exists(backupName): return False
        if not self._Speed == None:
            self._Speed['name'] = '打包数据库%s成功==>OK' % name
            self._Speed['current'] = 'database'
            self.WriteLogs(json.dumps(self._Speed))
        return backupName

    def test_send(self,get):
        ret=self.send_database(str(get.database))
        return ret

    # 设置密码
    def set_password(self,name):
        for i in self._site_info['databases']:
            if i['name']==name:
                return i['password']
        else:
            ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 32))
            return ran_str

    #新建数据库
    def insert_database(self,database):
        error='''"status": false'''
        data = self.get_key_data()
        data['name']=database
        data['codeing']='utf8'
        data['db_user']=database
        data['password']=self.set_password(database)
        data['dtype']='MySQL'
        data['dataAccess']='127.0.0.1'
        data['address']='127.0.0.1'
        data['ps']=database
        ret = self._request.post(self.__BT_PANEL + '/database?action=AddDatabase', data=data)
        if error in ret.text: return False
        ret=json.loads(ret.text)
        return ret

    #导入数据库
    def set_database_table(self,database,path):
        error = '''"status": false'''
        data = self.get_key_data()
        data['name']=database
        data['file']=path
        ret = self._request.post(self.__BT_PANEL + '/database?action=InputSql', data=data)
        if error in ret.text: return False
        if not self._Speed == None:
            self._Speed['name'] = '数据库:%s写入数据表成功==>OK' % database
            self.WriteLogs(json.dumps(self._Speed))
        ret=json.loads(ret.text)
        return ret

    # 删除遗留文件
    def del_database(self,path):
        data = self.get_key_data()
        data['path']=path
        self._request.post(self.__BT_PANEL + '/files?action=DeleteFile', data=data)

    # 发送ftp
    def send_ftps2(self,ftp,all=False):
        if all:
            error = '''"status": false'''
            data = self.get_key_data()
            for i in self._site_info['ftps']:
                data['ftp_username'] = i['name']
                data['ftp_password'] = i['password']
                data['path'] = i['path']
                data['ps'] = i['ps']
                ret = self._request.post(self.__BT_PANEL + '/ftp?action=AddUser', data=data)
                if error in ret.text: status = False
                status = True
                ftp_info = {}
                ftp_info['user'] = i['name']
                ftp_info['status'] = status
                self._ftp_info.append(ftp_info)
        else:
            error = '''"status": false'''
            data = self.get_key_data()
            for i in self._site_info['ftps']:
                if i['name']==ftp:
                    data['ftp_username']=i['name']
                    data['ftp_password']=i['password']
                    data['path']=i['path']
                    data['ps']=i['ps']
                    ret=self._request.post(self.__BT_PANEL + '/ftp?action=AddUser', data=data)
                    if error in ret.text: status=False
                    status=True
                    ftp_info={}
                    ftp_info['user']=i['name']
                    ftp_info['status']=status
                    self._ftp_info.append(ftp_info)
        return self._ftp_info

    def __get_md5(self, s):
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()

    def upload_file(self, upload_path,file_path):
        pdata = self.get_key_data()
        pdata['f_path'] = upload_path
        self._request = requests.session()
        if not os.path.isdir(file_path):
            return self.start_upload(pdata, file_path)
        n = 0
        size = 0
        for d_info in os.walk(file_path):
            pdata['f_path'] = (upload_path + '/' + d_info[0].replace(file_path, '')).replace('//', '/')
            for name in d_info[2]:
                filename = os.path.join(d_info[0], name)
                pdata['f_size'] = os.path.getsize(filename)
                print(filename + ',size:%s' % pdata['f_size']),
                if not self._Speed==None:
                    self._Speed['Current_file']='正在发送文件%s'%filename
                    self.WriteLogs(json.dumps(self._Speed))

                self.start_upload(pdata, filename)
                if not self._Speed==None:
                    self._Speed['Current_file']='发送完成%s====>OK'%filename
                    self.WriteLogs(json.dumps(self._Speed))
                print(' ==> OK')
                n += 1
                size += pdata['f_size']
        print('successify: %s,size:%s' % (n, (size / 1024 / 1024)))

    # 设置权限
    def set_chome(self, file_chmoe, file_path):
        for i in file_chmoe:
            data = self.get_key_data()
            data['filename'] = (file_path + '/' + i['path']).replace('//', '/')
            data['user'] = i['info']['chown']
            data['access'] = i['info']['chmod']
            data['all'] = True
            ret = self._request.post(self.__BT_PANEL + '/files?action=SetFileAccess', data=data)
            print(ret.text)
        return True

    # 获取本地目录权限
    def get_chome(self, file_path):
        ret = None
        if not os.path.isdir(file_path):
            path_info = {}
            path = file_path
            info = self.GetFileAccess(path)
            path_info['path'] = file_path
            path_info['info'] = info
            self._chmoe.append(path_info)
            return self._chmoe
        else:
            for d_info in os.walk(file_path):
                ret = d_info
                break
            cc = ret[1] + ret[2]
            for i in cc:
                path_info = {}
                path = file_path + '/' + i
                info = self.GetFileAccess(path)
                path_info['path'] = i
                path_info['info'] = info
                self._chmoe.append(path_info)
            return self._chmoe

    # 获取文件/目录 权限信息
    def GetFileAccess(self, filename):
        if sys.version_info[0] == 2: filename = filename.encode('utf-8');
        data = {}
        try:
            import pwd
            stat = os.stat(filename)
            data['chmod'] = str(oct(stat.st_mode)[-3:])
            data['chown'] = pwd.getpwuid(stat.st_uid).pw_name
        except:
            data['chmod'] = 755
            data['chown'] = 'www'
        return data

    def get_filename(self, filename):
        return filename.split('/')[-1]

    def start_upload(self, pdata, filename):
        mode_file = self.GetFileAccess(filename)
        mode_dir = self.GetFileAccess(pdata['f_path'])
        if not 'f_size' in pdata: pdata['f_size'] = os.path.getsize(filename)
        pdata['f_start'] = 0
        pdata['f_name'] = self.get_filename(filename)
        pdata['action'] = 'upload'
        pdata['dir_mode']= "%s,%s" % (mode_dir['chmod'],mode_dir['chown'])
        pdata['file_mode']= "%s,%s" % (mode_file['chmod'],mode_file['chown'])
        f = open(filename, 'rb')
        ret = self.send_file_to(pdata, f)
        return ret

    def send_file_to(self, data, f):
        max_size = 1024 * 1024 * 2
        f.seek(data['f_start'])
        f_end = max_size
        t_end = data['f_size'] - data['f_start']
        if t_end < max_size: f_end = t_end
        files = {'blob': f.read(f_end)}
        ret = self._request.post(self.__BT_PANEL + '/files', data=data, files=files)
        if re.search('^\d+$', ret.text):
            data['f_start'] = int(ret.text)
            return self.send_file_to(data, f)
        else:
            return ret.text

if __name__ == '__main__':
    my_api = psync_api_main()
    r_data = my_api.start_transfer()