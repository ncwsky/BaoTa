#!/usr/bin/python
# coding: utf-8
#  Author: 带头大哥
import sys, os, json
os.chdir("/www/server/panel")
sys.path.append("class/")
import public,re

class sshkey_main():

    # 开启密码登陆
    def SetPassword(self,get):
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file = public.readFile('/etc/ssh/sshd_config')
        if len(re.findall(ssh_password, file)) == 0:
            file_result=file+'\nPasswordAuthentication yes'
        else:
            file_result = re.sub(ssh_password, '\nPasswordAuthentication yes', file)
        self.Wirte('/etc/ssh/sshd_config', file_result)
        self.RestartSsh()
        return public.returnMsg(True, '开启成功')

    #设置ssh_key
    def SetSshKey(self,get):
        ''''''
        type_list=['rsa','dsa']
        ssh_type=['yes','no']
        ssh=get.ssh
        if not ssh in ssh_type:return public.returnMsg(False,'ssh选项失败')
        type=get.type
        if not type in type_list:return public.returnMsg(False,'加密方式错误')
        file=['/root/.ssh/id_rsa.pub','/root/.ssh/id_rsa','/root/.ssh/authorized_keys']
        for i in file:
            if os.path.exists(i):
                os.remove(i)
        os.system("ssh-keygen -t %s -P '' -f ~/.ssh/id_rsa |echo y"%type)
        if os.path.exists(file[0]):
            public.ExecShell('cat %s >%s && chmod 600 %s'%(file[0],file[-1],file[-1]))
            rec = '\n#?RSAAuthentication\s\w+'
            rec2 = '\n#?PubkeyAuthentication\s\w+'
            file=public.readFile('/etc/ssh/sshd_config')
            if len(re.findall(rec, file)) == 0:file=file+'\nRSAAuthentication yes'
            if len(re.findall(rec2, file)) == 0: file = file + '\nPubkeyAuthentication yes'
            file_ssh=re.sub(rec, '\nRSAAuthentication yes', file)
            file_result=re.sub(rec2, '\nPubkeyAuthentication yes', file_ssh)
            if ssh=='no':
                ssh_password='\n#?PasswordAuthentication\s\w+'
                if len(re.findall(ssh_password, file_result)) == 0:
                    file_result = file_result + '\nPasswordAuthentication no'
                else:
                    file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file_result)
            self.Wirte('/etc/ssh/sshd_config',file_result)
            self.RestartSsh()
            return public.returnMsg(True, '开启成功')
        else:
            return public.returnMsg(False, '开启失败')

    # 关闭sshkey
    def StopKey(self,get):
        file = ['/root/.ssh/id_rsa.pub', '/root/.ssh/id_rsa', '/root/.ssh/authorized_keys']
        rec = '\n#?RSAAuthentication\s\w+'
        rec2 = '\n#?PubkeyAuthentication\s\w+'
        file = public.readFile('/etc/ssh/sshd_config')
        file_ssh = re.sub(rec, '\n#RSAAuthentication no', file)
        file_result = re.sub(rec2, '\n#PubkeyAuthentication no', file_ssh)
        self.Wirte('/etc/ssh/sshd_config', file_result)
        self.SetPassword(get)
        self.RestartSsh()
        return public.returnMsg(True, '关闭成功')

    # 读取配置文件 获取当前状态
    def GetConfig(self,get):
        result={}
        file = public.readFile('/etc/ssh/sshd_config')
        rec = '\n#?RSAAuthentication\s\w+'
        pubkey='\n#?PubkeyAuthentication\s\w+'
        ssh_password = '\nPasswordAuthentication\s\w+'

        ret=re.findall(ssh_password, file)
        if not ret:
            result['password'] = 'no'
        else:
            if ret[-1].split()[-1]=='yes':
                result['password']='yes'
            else:
                result['password']='no'

        pubkey = re.findall(pubkey, file)
        if not pubkey:
            result['pubkey'] = 'no'
        else:
            if pubkey[-1].split()[-1] == 'no':
                result['pubkey'] = 'no'
            else:
                result['pubkey'] = 'yes'

        rsa_auth = re.findall(rec, file)
        if not rsa_auth:
            result['rsa_auth'] = 'no'
        else:
            if rsa_auth[-1].split()[-1] == 'no':
                result['rsa_auth'] = 'no'
            else:
                result['rsa_auth'] = 'yes'
        return result


    # 关闭密码方式
    def StopPassword(self,get):
        file = public.readFile('/etc/ssh/sshd_config')
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file)
        self.Wirte('/etc/ssh/sshd_config', file_result)
        self.RestartSsh()
        return public.returnMsg(True, '关闭成功')


    #显示key文件
    def GetKey(self,get):
        file = '/root/.ssh/id_rsa'
        if not  os.path.exists(file):return public.returnMsg(True, '')
        ret=public.readFile(file)
        return public.returnMsg(True, ret)

    #下载
    def Download(self,get):
        'http://liang.o2oxy.cn:8888/download?filename=%2Fwww%2Fcurrbackup.py'
        if os.path.exists('/root/.ssh/id_rsa'):
            ret='/download?filename=/root/.ssh/id_rsa'
            return public.returnMsg(True, ret)

    #写入配置文件
    def Wirte(self,file,ret):
        result=public.writeFile(file,ret)
        return result

    def RestartSsh(self):
        version = public.readFile('/etc/redhat-release')
        act = 'restart'
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act)
        elif version.find(' 7.') != -1:
            public.ExecShell("systemctl " + act + " sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd " + act)
