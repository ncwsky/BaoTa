# coding: utf-8
# 送给支持宝塔的各位
# Author: 带头大哥
import sys, os
import time
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import  public, json,re,firewalls,base64

nfs_settings = {
    '读取方式': {'ro': '只读', 'rw': '读写'},
    '写入方式': {'sync': '数据同步写入到内存与硬盘中', 'async': '数据会先暂存于内存中，而非直接写入硬盘'},
    '权限': {'root_squash': 'root映射成anonymous权限(默认)', 'no_root_squash': '客户机用root访问该共享文件夹时，不映射root用户'},
    '映射方式': {'all_squash': '客户机上的任何用户访问该共享目录时都映射成匿名用户', 'no_all_squash': '保留共享文件的UID和GID(默认)'},
    'uid': {'anonuid': '将客户机上的用户映射成指定的本地用户ID的用户'},
    'gid': {'anongid': '将客户机上的用户映射成属于指定的本地用户组ID'},
}

class addport: port = ps = ''
class nfsserver_main(object):
    __path = '/www/server/panel/plugin/nfsserver'
    __config='/www/server/panel/plugin/nfsserver/user.json'
    __nfsconfig='/etc/exports'
    __system_mount='/www/server/panel/plugin/nfsserver/mount.json'

    def __init__(self):
        if not os.path.exists(self.__path):
            os.mkdir(self.__path)
        self.SetFirewalld()

    # NFS 需要的端口才能正常运行
    def SetFirewalld(self):
        fs = firewalls.firewalls()
        get = addport()
        port_list=[32803,32769,662,892,111,2049]
        for i in port_list:
            get.port=str(i)
            get.ps = 'nfsserver插件所需端口'
            fs.AddAcceptPort(get)

    def SetConfig(self,get):
        path= get.path
        type = get.type
        ip=get.ip
        ret=json.loads(get.ret)
        if not os.path.exists(path):return public.returnMsg(True, '目录不存在')
        site=''
        result_data=[]
        result={}
        if type=='0':
            ip='*'
            #'/tmp  *(rw)'
            if not self.DictoJson(ret):return public.returnMsg(False, '请选择权限列表');
            site=path+'   '+'*'+'('+ self.DictoJson(ret)+ ')'
        elif type=='1':
            #'/tmp  192.168.10.*(rw)'
            if not self.DictoJson(ret): return public.returnMsg(False, '请选择权限列表');
            if not self.Repath(ip,type=1):return public.returnMsg(False, 'FIREWALL_IP_FORMAT');
            site = path + '   ' + ip +'('+ self.DictoJson(ret)+ ')'
        elif type=='2':
           # '/tmp 192.168.10.100(rw)'
            if not self.DictoJson(ret): return public.returnMsg(False, '请选择权限列表');
            if not self.Repath(ip, type=2): return public.returnMsg(False, 'FIREWALL_IP_FORMAT');
            site = path + '   ' + ip  +'('+ self.DictoJson(ret)+ ')'
        elif type == '3':
            # '/tmp *.aa.com(rw)'
            if not self.DictoJson(ret): return public.returnMsg(False, '请选择权限列表');
            if not self.Repath(ip, type=3): return public.returnMsg(False, '只支持*.aa.com');
            site = path + '   ' + ip  +'('+ self.DictoJson(ret)+ ')'
        elif type=='4':
            # '/tmp aa.aa.com(rw)'
            if not self.DictoJson(ret): return public.returnMsg(False, '请选择权限列表');
            if not self.Repath(ip, type=4): return public.returnMsg(False, '只支持二级域名');
            site = path + '   ' + ip  +'('+ self.DictoJson(ret)+ ')'
        result['path']=path
        result['ret']=ret
        result['ip']=ip
        result['site']=site
        result['id']=self.GetRandomString(20)
        retc=self.SetUserConfig(result)
        if not retc:return public.returnMsg(False,'已经存在')
        self.Config(result)
        result_data.append(result)
        self.Reload()
        return public.returnMsg(True, '添加成功')

    # 配置文件控制
    def Config(self,data):
        ret=public.ReadFile(self.__nfsconfig)
        if not ret:
            rec=data['site']+'\n'
            public.WriteFile(self.__nfsconfig,rec)
        else:
            rec = data['site'] + '\n'
            public.WriteFile(self.__nfsconfig, rec,mode='a+')

    def Reload(self):
        public.ExecShell('exportfs -r')

    # 存入数据文件
    def SetUserConfig(self,data):
        if not os.path.exists(self.__config):
            ret=[]
            ret.append(data)
            public.WriteFile(self.__config,json.dumps(ret))
            return True
        else:
            ret=json.loads(public.ReadFile(self.__config))
            if not ret:
                ret = []
                ret.append(data)
                public.WriteFile(self.__config, json.dumps(ret))
                return True
            else:
                if len(ret)>=1:
                    for i in ret:
                        if i['path']==data['path'] and i['ret']==data['ret'] and i['ip']==data['ip']:
                            return False
                    ret.append(data)
                    public.WriteFile(self.__config, json.dumps(ret))
                    return True
                else:
                    ret = []
                    ret.append(data)
                    public.WriteFile(self.__config, json.dumps(ret))
                    return True

    #删除数据
    def DelUserConfig(self,get):
        type_id=get.id
        aa=[]
        if not os.path.exists(self.__config):return aa
        ret=json.loads(public.ReadFile(self.__config))
        for i in ret:
            if i['id']==type_id:
                self.DelConfig(i['site'])
                ret.remove(i)
        public.WriteFile(self.__config, json.dumps(ret))
        self.Reload()
        return public.returnMsg(True, '删除成功')

    #配置文件删除
    def DelConfig(self,data):
        ret=public.ReadFile('/etc/exports')
        ret=ret.replace(data,'')
        try:
            if len(ret)==1:
                resutl=''
            if ret[0]=='\n' and ret[-1]=='\n':
                resutl=ret[1:-1]
            elif ret[0]=='\n':
                resutl = ret[1:]
            else:
                resutl=ret
        except:
            resutl = ''
        public.WriteFile('/etc/exports',resutl)

    # 作为标识ID
    def GetRandomString(self,length):
        from random import Random
        strings = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        chrlen = len(chars) - 1
        random = Random()
        for i in range(length):
            strings += chars[random.randint(0, chrlen)]
        return strings

    #转换前端传递过来的数据
    def DictoJson(self,data):
        if len(data)==0:
            return False
        if len(data)==1:
            return data[0]
        else:
            ac=','.join(data)
            return ac

    def ReturnSitings(self,get):
        return public.returnMsg(True, nfs_settings)

    # 正则匹配
    def Repath(self,data,type=1):
        if type==1:
            rep = '\d+\.\d+\.\d+\.\*'
            if not re.search(rep, data): return False
            return True
        elif type==2:
            rep = "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            if not re.search(rep, data): return False
            return True
        elif type==3:
            rep = "^\*.\w+.\w+"
            if not re.search(rep, data): return False
            return True
        elif type==4:
            rep = "^\w+.\w+.\w+"
            if not re.search(rep, data): return False
            return True

    # 返回挂载的数据
    def GetUser(self,get):
        aa=[]
        if not os.path.exists(self.__config): return aa
        ret = json.loads(public.ReadFile(self.__config))
        if not ret: return public.returnMsg(False, '配置文件为空')
        return public.returnMsg(True, ret)

    # 秘钥
    def GetMisc(self,get):
        type_id = get.id
        ip=get.ip
        if not os.path.exists(self.__config): return public.returnMsg(False, '未存在配置文件')
        ret = json.loads(public.ReadFile(self.__config))
        if not ret: return public.returnMsg(False, '配置文件为空')
        for i in ret:
            if i['id'] == type_id:
                ret={}
                ret['ip']=ip
                ret['path']=i['path']
                return public.returnMsg(True,base64.b64encode(json.dumps(ret)))
        return public.returnMsg(False, '不存在')

    #公网地址
    def IPaddress(self,get):
        data={}
        data['wai']=public.GetLocalIp()
        ip=self.GetIp()
        if ip=='127.0.0.1' or ip=='0.0.0.0':
            pass
        else:
            data['nei']=ip
        return data

    # 内网地址
    def GetIp(self):
        import psutil
        netcard_info = []
        info = psutil.net_if_addrs()
        for k, v in info.items():
            for item in v:
                ret={}
                if item[0] == 2 and not item[1] == '127.0.0.1':
                    ret[k]=item[1]
                    netcard_info.append(ret)
        return netcard_info


    def GetIp2(self):
        import socket
        import platform
        def getip():
            try:
                s = socket.socket(socket.AF_INET, socket.SO_DEBUG)
                s.connect(('www.baidu.com', 0))
            except:
                ip = "0.0.0.0"
            finally:
                s.close()
            return ip
        sys_a = platform.system()
        ip = socket.gethostbyname(socket.gethostname())
        return ip

    def Restart(self):
        version = public.readFile('/etc/redhat-release')
        act = 'restart'
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service rpcbind start')
            public.ExecShell('service nfs start')
        elif version.find(' 7.') != -1:
            public.ExecShell('systemctl ' + act + ' rpcbind.service')
            public.ExecShell('systemctl ' + act + 'nfs-server.service')
        else:
            public.ExecShell('systemctl ' + act + ' rpcbind.service')
            public.ExecShell('systemctl ' + act + 'nfs-server.service')
            public.ExecShell('service rpcbind start')
            public.ExecShell('service nfs start')




    #---------------------NFS 客户端挂载
    def Client(self,get):
        misc=get.misc
        os_path=get.path
        try:
            path=base64.b64decode(misc)
            aa = json.loads(path)
            ip=aa['ip']
            path=aa['path']
            if not os.path.exists(os_path):public.ExecShell('mkdir -p %s'%os_path)
            ret=self.Mount(ip,path,os_path)

            if ret:
                return public.returnMsg(True, '挂载成功')
            else:
                return public.returnMsg(False, '挂载失败')
        except:
            return public.returnMsg(False, '请输入正确的秘钥')

    # 挂载
    def Mount(self,ip,path,os_path):
        ret=public.ExecShell("mount -t nfs %s:%s %s"%(ip,path,os_path))
        retc='denied|exist'
        if not re.search(retc, ret[-1]):
            return True
        else:
            return False

    # 查看挂载
    def GetSystemSize(self,get):
        type='system'
        if type == 'system':
            cmd_get_hd_use = '/bin/df'
        elif type == 'Inode':
            cmd_get_hd_use = '/bin/df -i'
        else:
            return public.ReturnMsg(False, '类型错误')
        try:
            fp = os.popen(cmd_get_hd_use)
        except:
            ErrorInfo = r'get_hd_use_error'
            return (ErrorInfo)
        re_obj = re.compile(r'^\d+.\d+.\d+.\d+(?P<used>.+)%\s+(?P<mount>.+)')
        hd_use = {}
        for line in fp:
            match = re_obj.search(line)
            if match:
                hd_use[match.groupdict()['mount']] = match.groupdict()['used']
        fp.close()
        return public.returnMsg(True, hd_use)

    # 存放在文件中
    def SetSystem(self,data):
        if not os.path.exists(self.__system_mount):
            file = open(self.__system_mount, 'w')
            file.close()
            public.WriteFile(self.__system_mount,json.dumps(data))
            return True
        else:
            ret=public.ReadFile(self.__system_mount)
            if not ret:
                public.WriteFile(self.__system_mount, json.dumps(data))
                return True
            else:
                if len(ret)>=1:
                    for i in ret.keys():
                        pass
                    pass
                else:
                    public.WriteFile(self.__system_mount, json.dumps(data))
                    return True

            pass

    # 卸载挂载的
    def Umount(self,get):
        path=get.path
        if not os.path.exists(path):return public.returnMsg(False, '文件夹不存在')
        public.ExecShell('umount %s'%path)
        return public.returnMsg(True, '卸载成功')
