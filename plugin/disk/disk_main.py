#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: xf <1196323914@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------

#+--------------------------------------------------------------------
import sys,os,json,time

#设置运行目录
os.chdir("/www/server/panel")

#添加包引用位置并引用公共包
sys.path.append("class/")
import public

#from common import dict_obj
#get = dict_obj();


#在非命令行模式下引用面板缓存和session对象
if __name__ != '__main__':
    from BTPanel import cache,session

    #设置缓存(超时10秒) cache.set('key',value,10)
    #获取缓存 cache.get('key')
    #删除缓存 cache.delete('key')

    #设置session:  session['key'] = value
    #获取session:  value = session['key']
    #删除session:  del(session['key'])


class disk_main:
    __plugin_path = "/www/server/panel/plugin/disk/"
    __config = None
    __mount_file="/etc/fstab"
    __check_file=__plugin_path+'check_file.sh'

    #构造方法
    def  __init__(self):
        os.system('echo "- - -" > /sys/class/scsi_host/host1/scan ')
        os.system('echo "- - -" > /sys/class/scsi_host/host2/scan ')
        os.system('echo "- - -" > /sys/class/scsi_host/host3/scan ')

        #centos7  /etc/locale.conf  LANG="zh_CN.UTF-8"
        #centos6  /etc/sysconfig/i18n  LANG="en_US.UTF-8"
        #mkfs -t ext4 /dev/sdb2
        # e2fsck - p / dev / sdb1
        # public.ExecShell('fdisk -l |grep -E "Disk /.*?|磁盘 /dev/.*?"')

    def ToSize(self,size):
            ds = ['b','KB','MB','GB','TB']
            for d in ds:
                if size < 1024: return str(size)+d
                size = size / 1024
            return '0b';
    def check_time(self):
        import urllib2
        import time
        ret = urllib2.urlopen('http://www.baidu.com')
        ts = ret.headers.get("Date")
        ltime = time.strptime(ts[5:25], "%d %b %Y %H:%M:%S")
        now_time = time.mktime(ltime)
        if now_time > 1556683200: #5.1      1556683200
            return False
        else:
            return True

    def disk_format(self,path):
        ret=public.ExecShell("export LANG='en_US.UTF-8' && cat /etc/fstab |grep %s|awk '{print $3}'|head -1"%path)[0]
        ret=ret if len(ret) >1 else ""
        return ret.strip()
    def get_info(self,args):

        data = []
        import re
        dev=public.ExecShell('fdisk -l |grep -E "Disk /dev/.*?:|磁盘 /dev/.*?："')[0].strip().split('\n')
        #中英文不一样****
        if sys.version_info[0] == 2:
            dev = [re.compile("/.*?：|/.*?:").findall(i.encode("utf-8"))[0].replace(":","").replace("：","") for i in dev]
        else:
            dev = [re.compile("/.*?：|/.*?:").findall(i)[0].replace(":","").replace("：", "") for i in dev]

        for i in dev:
            if i.find("swap") !=-1:continue
            tmp={}
            tmp['path']=i
            tmp['disk_format']=self.disk_format(i)
            tmp['status']=self.check_mount_status(i)
            tmp['name']=self.check_mount_name(i)
            if tmp['name'].find("和")!=-1:
                tmp['size']=self.check_mount_size(i)
            else:
                tmp_name=tmp['path'] if len(tmp['name'])>=1 else tmp['name']
                tmp['size'] = self.check_mount_size(tmp_name)
            data.append(tmp)
        return sorted(data,key=lambda x:x['path'])

    def check_mount_size(self,path):
        size=public.ExecShell('''export LANG='en_US.UTF-8' && df -lh |grep %s |awk 'NR==1{print $3,"/",$2}' '''%path)[0]
        if len(size)<2:
            size =public.ExecShell('''export LANG='en_US.UTF-8' && fdisk -l |grep %s |awk '{print $3,$4}'  '''%path)[0]
        size=size.split(",")[0]
        return size
    def check_mount_status(self,path):#0表示挂载 1表示未挂载
        status=os.system("df -lh |grep %s"%path)
        if status==0:
            return 0
        else:return 1

    def check_mount_name(self,path):
        name=public.ExecShell("df -lh |grep %s |awk '{print $NF}'"%path)[0].strip()
        name=name.replace("\n","和")
        if not name:name=path
        return name

    def get_file_size(self,name):
        if os.path.exists(name):
            size = public.ExecShell("du -s %s |awk '{print $1}'" % name)[0].strip()
        else:size=0
        return size

    def CheckFilename(self,get):
        name=get.path #/opt
        addr=get.addr  #/dev/sdb
        import re
        name = re.compile('\/?[a-zA-Z]+|\/').findall(name)
        if len(name) != 1:
            return {'status':False,'msg': '文件名错误'}
        name=name[0]
        if name.find('/') == -1:
            name = "/" + name
        if name in ['/etc','/','/root','/var','/boot','/home','/bin','/dev','/srv','/usr','/lib','/lib64','/sys','/proc','/sbin']:
            return {'status': False, 'msg': '系统文件禁止操作'}
        if addr.find("swap") !=-1:
            return {'status': False, 'msg': 'swap分区无法挂载'}
        handle=get.handel
        if handle=="挂载":
            #准备挂载
            if name=='/www':
                name_size=public.ExecShell("du -bs %s |awk '{print $1}'"%name)[0].strip()
                disk_size=public.ExecShell("export LANG='en_US.UTF-8' && fdisk -l |grep -E 'Disk %s|磁盘 %s' |awk '{print $5}'"%(addr,addr))[0].strip()
                if int(name_size)>int(disk_size):
                    return {'status': False, 'msg': "新磁盘容量不够，无法迁移"}
                return {'status': True,'msg':"即将迁移数据到新硬盘!请确保停止web服务和mysql服务"}
            if os.system("df -lh |grep %s"%name)==0:
                return {'status':False,'msg': '无法覆盖挂载'}

            ret=os.path.exists(name)
            if ret:
                return {'status': True,'msg':'文件名已存在，挂载后将覆盖数据，请确保数据已备份！'}
            return {'status': True,'msg':""}
        else:
            if name == '/www':
                return {'status': False, 'msg': "请手动卸载"}
            return {'status':True,'msg':"请确保卸载目录已备份"}

    def MountFile(self,get):
        formats = get.formats
        path=get.path  #/opt
        name=get.addr  #/dev/sdb
        handle = get.handel
        if path.find('/') == -1:
            path = "/" + path
        t_name = name + "1"
        if handle == "挂载":
            if path == '/www':#改名
                back_name = path + '_backup'
                self.__write_logs("迁移数据%s 到新硬盘%s" % (path,name))
                os.system("mv %s %s" % (path, back_name))
                if not os.path.exists(back_name):
                    return {'msg':'挂载失败文件不存在','status':False}
            if not os.path.exists(path):os.mkdir(path)
            public.ExecShell('''echo -e "n\np\n\n\n\nt\\n8e\nw"| fdisk %s '''%name)
            public.ExecShell("mkfs -t %s %s"%(formats,t_name))
            public.ExecShell("e2fsck - p %s"%t_name)
            if os.system("cat /etc/fstab | grep '%s '"%path)==0:
                public.ExecShell("sed -i 's@^#%s %s@%s %s@g' /etc/fstab && mount -a"%(t_name,path,t_name,path))
            else:
                public.ExecShell("echo '%s %s  %s  defaults 0 0 \n'>> /etc/fstab && mount -a"%(t_name,path,formats))
            if path == '/www':
                b=path+'_backup'
                os.system("nohup echo test > /tmp/copy_www.pid && bash %s &"%self.__check_file)
                os.system("nohup cp -arf {1}/* {0}/ && rm -f /tmp/copy_www.pid && sleep 3 && /etc/init.d/bt restart &".format('/www','/www_backup'))
                return {'msg': '正在备份数据请稍等', 'status': True, 'copyfile': True}
            self.__write_logs("用户挂载磁盘[%s]到[%s]" % (name, path))
            return {'msg':'挂载成功！请在首页查看','status':True}
        else:
            if os.system("cat /etc/fstab | grep '%s '" % path) == 0:
                public.ExecShell("sed -i 's@^%s %s  %s  defaults 0 0@@g' /etc/fstab && mount -a" % (t_name,path,formats))
                public.ExecShell("fuser -km %s"%path)
                public.ExecShell("umount %s && echo 'y'|mkfs.%s %s"%(path,formats,name))
            else:
                public.ExecShell("fuser -km %s" % path)
                public.ExecShell("umount %s && echo 'y'|mkfs.ext4 %s" % (path,name))
            self.__write_logs("用户卸载磁盘[%s]" % path)
            return {'msg':"卸载%s成功"%path,'status':True}

    def check_task(self,get):
        if os.path.exists('/tmp/copy_www.pid'):
            return {'msg': "正在迁移数据", 'status': True}
        else:return {'msg':"未发现任务",'status':False}

  # 获取进度
    def GetSpeed(self,get):
        try:
            path=get.path   # /www
            if path.find('/') == -1:
                path = "/" + path
            back_path=path+'_backup'
            if os.path.exists(path) and os.path.exists(back_path):
                used=int(public.ExecShell("du -bs %s |awk '{print $1}'"%path)[0].strip())
                total=int(public.ExecShell("du -bs %s |awk '{print $1}'"%back_path)[0].strip())
                pre = int((100.0 * used / total))
                if used>=total or pre>=99:return {'status':False,'use':used,'total':total,'msg':'成功迁移'}
                return {'status':True,'total':total,'used':used,'pre':pre,'name':'正在迁移文件'}
            else:
                return {'status':False,'msg':"未知错误"}
        except:
            return {'name': '准备部署', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}

    def search_log(self,get):
        info={'Refile':[],'Redir':[]}
        info['system_log'] = []
        path=get.path
        tmp =public.ExecShell("find %s -type f -size +10M 2>/dev/null|grep -E '*.log$|*.tar$|*.gz$'|xargs du -b --exclude=." % path)[0].strip()
        if len(tmp)==0:
            return info
        else:tmp=tmp.split("\n")
        for i in tmp:
            size,path=i.split()
            line={"size":size,"path":path}
            info['system_log'].append(line)

        return info

    def remove_file(self,get):
        ret = []
        data = json.loads(get.data)
        if 'system_log' in data:
            system_log=data['system_log']
            if len(system_log)!=0:
                for i in system_log:
                    # 统计
                    count_size=int(i['size'])
                    ret.append(count_size)
                    # 清理系统日志
                    os.remove(i['path'])
                # 进度条
                time.sleep(0.1)

        return self.ToSize(sum(ret))

    def GetToStatus(self,get):
        pass

    #获取面板日志列表
    #示例已登录面板的情况下访问get_logs方法：/plugin?action=a&name=demo&s=get_logs
    def get_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 12
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)

        #取日志总行数
        count = public.M('logs').where('type=?',(u'磁盘操作',)).count()

        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)

        #获取当前页的数据列表
        log_list = public.M('logs').where('type=?',(u'磁盘操作',)).order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()
        
        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }
    def del_log(self,get):
        ret=public.M('logs').where('type=?', (u'磁盘操作',)).delete()
        return public.returnMsg(True, '清理成功')

    def __write_logs(self,logstr):
        public.WriteLog('磁盘操作',logstr)

    #读取配置项(插件自身的配置文件)
    #@param key 取指定配置项，若不传则取所有配置[可选]
    #@param force 强制从文件重新读取配置项[可选]
    def __get_config(self,key=None,force=False):
        #判断是否从文件读取配置
        if not self.__config or force:
            config_file = self.__plugin_path + 'config.json'
            if not os.path.exists(config_file): return None
            f_body = public.ReadFile(config_file)
            if not f_body: return None
            self.__config = json.loads(f_body)

        #取指定配置项
        if key:
            if key in self.__config: return self.__config[key]
            return None
        return self.__config

    #设置配置项(插件自身的配置文件)
    #@param key 要被修改或添加的配置项[可选]
    #@param value 配置值[可选]
    def __set_config(self,key=None,value=None):
        #是否需要初始化配置项
        if not self.__config: self.__config = {}

        #是否需要设置配置值
        if key:
            self.__config[key] = value

        #写入到配置文件
        config_file = self.__plugin_path + 'config.json'
        public.WriteFile(config_file,json.dumps(self.__config))
        return True

