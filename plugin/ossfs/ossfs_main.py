# coding: utf-8
# 送给支持宝塔的各位
# Author: 带头大哥
import sys, os
import time
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel');
sys.path.append("class/")
import  public, json,re

class ossfs_main(object):
    __path='/www/server/panel/plugin/ossfs'
    __path_sh='/www/server/panel/plugin/ossfs/ossfs.sh'

    # 填写信息
    def GetUser(self,get):
        '''
        传入三个值:
        my-bucket (这个是oss的一个Backet名称)
        :my-access-key-id  (这个是OSS 的key_id)
        :my-access-key-secret (这个是oss的 key)
        :path 需要挂载的目录
        :registy 挂载的一个url

        :param get:
        :return:
        '''
        backet=get.backet.strip()
        access_id=get.access_id.strip()
        access_key=get.access_key.strip()
        path = get.path.strip()
        registy = get.registy.strip()
        if not backet and not access_id and not access_key:return public.returnMsg(False,'填写好你的信息哦')
        public.ExecShell("echo '%s:%s:%s' >/etc/passwd-ossfs"%(backet,access_id,access_key))
        public.ExecShell('chmod 640 /etc/passwd-ossfs')
        ret=self.Mount(backet,path,registy)
        user_info={}
        user_info['backet']=backet
        user_info['access_id']=access_id
        user_info['access_key']=access_key
        user_info['path']=path
        user_info['registy']=registy
        user=self.__path+'/user.json'
        public.writeFile(user, json.dumps(user_info))
        return ret

    def Mount(self,backet,path,oss_path):
        if not os.path.exists(path):
            return public.returnMsg(False,'挂载目录不存在')
        rets='/etc/passwd-ossfs'
        if not os.path.exists(rets):return public.returnMsg(False,'信息验证失败')
        ret=self.Check_ossfs()
        if not ret:return ret
        public.ExecShell('/usr/local/bin/ossfs %s %s -ourl=%s'%(backet,path,oss_path))
        retc='ossfs %s %s -ourl=%s'%(backet,path,oss_path)
        public.writeFile(self.__path_sh,retc)
        public.ExecShell('chmod +x %s'%self.__path_sh)
        self.ChekcInit()
        check=self.CheckMount()
        if not check:return public.returnMsg(False,'挂载失败%s'%path)

        if path in check[0]:
            return public.returnMsg(True,'挂载成功[%s]'%path)
        else:
            return public.returnMsg(False,'挂载失败%s'%path)

    # 开机自启动
    def ChekcInit(self):
        if  os.path.exists(self.__path_sh):
            rc_local='/etc/rc.local'
            rcinit=public.readFile(rc_local)
            ret='/www/server/panel/plugin/ossfs/ossfs.sh'
            check_local=re.findall(ret,rcinit)
            if not check_local:
                public.ExecShell("echo 'bash /www/server/panel/plugin/ossfs/ossfs.sh'>>/etc/rc.local")

    # 卸载的时候去掉
    def Delsh(self):
        if os.path.exists(self.__path_sh):
            os.remove(self.__path_sh)

    # 验证是否挂载成功
    def CheckMount(self):
        ret=public.ExecShell('df')
        rec='\n(oss\w+).+%\s+(.+)'
        ac=re.findall(rec,ret[0])
        if len(ac)==0:
            return False
        else:
            return ac

    # 状态
    def GetStatus(self,get):
        info=self.GetUserInfo(get)
        try:
            path=info['path']
            check = self.CheckMount()
            if not check: return public.returnMsg(False,'未挂载')
            if path in check[0]:
                return public.returnMsg(True,'挂载中')
            else:
                return public.returnMsg(False,'未挂载')
        except:
            return public.returnMsg(False, '未挂载')


    # 查看ossfs 是否安装
    def Check_ossfs(self):
        ret=int(public.ExecShell('which ossfs |grep ossfs|wc -l')[0])
        if ret==0:return public.returnMsg(False,'未安装ossfs')
        return True

    # 卸载
    def Umount(self,get):
        user=self.__path+'/user.json'
        self.Delsh()
        if not os.path.exists(user):
            return public.returnMsg(False,'未配置ossfs')
        user_info = json.loads(public.readFile(user))
        path=user_info['path']
        if path=='':
            return public.returnMsg(False,'未挂载')
        check=self.CheckMount()
        if not check:return public.returnMsg(True,'卸载成功')
        if path in check[0]:
            public.ExecShell('fusermount -u %s'%path)
        check2 = self.CheckMount()
        if not check2: return public.returnMsg(True, '卸载成功')
        if path in check2[0]:
            public.ExecShell('umount %s'%path)
        check3 = self.CheckMount()
        if not check3: return public.returnMsg(True, '卸载成功')
        if path in check3[0]:
            return public.returnMsg(False,'卸载失败，磁盘被占用,检查磁盘后尝试：例如:lsof /www')
        return public.returnMsg(True,'卸载成功')

    # 查看信息
    def GetUserInfo(self,get):
        user = self.__path + '/user.json'
        if not os.path.exists(user):
            return public.returnMsg(False, '')
        user_info = json.loads(public.readFile(user))
        return user_info