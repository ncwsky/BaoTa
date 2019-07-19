#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 刘佳东 <1548429568@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   守护进程管理器
#+--------------------------------------------------------------------
import sys,os,json,re,time
# 设置运行目录  
os.chdir("/www/server/panel")
# 添加包引用位置并引用公共包  
sys.path.append("class/")
import public
  
  
class supervisor_main:
    basedir = "/www/server/panel/plugin/supervisor"
    supervisor_conf_file = "/etc/supervisor/supervisord.conf"
    supervisor_conf_back = "/etc/supervisor/supervisord_back.conf"
    # 每个进程配置文件夹
    profile = "%s/profile/" % basedir
    # 所有进程日志文件夹
    log = "%s/log/" % basedir
    # 进程信息详情文件
    conf = "%s/config.json" % basedir
  
    # 终端输出日志文件
    logpath = "%s/terminal.out" % basedir
    # 进程状态临时文件
    status = "%s/status.txt" % basedir
    # 用户列表临时文件
    user = "%s/user.txt" % basedir
    
    # 守护进程列表
    def GetPorcessList(self, get):
        if not os.path.isfile(self.status):
            os.system(r"touch {}".format(self.status))
        res = public.ExecShell("supervisorctl status > %s" % self.status)
        with open(self.status,"r") as fr:
            lines = fr.readlines()
        fr.close()

        if lines:
            for r in lines:
                if "supervisor.sock" in r:
                    res = public.ExecShell("supervisord -c /etc/supervisor/supervisord.conf")
                    result = public.ExecShell("supervisorctl status > %s" % self.status)
                    with open(self.status,"r") as fr:
                        lines = fr.readlines()
                    fr.close()
                if "未找到命令" in r:
                    return public.ReturnMsg(False,'请先安装supervisor!') 
        os.remove(self.status)
  
        array_list = []
        for r in lines:
            if "FATAL" in r or "error" in r or "BACKOFF" in r:
                continue
            array = r.split()
            if array:
                d = dict()
                d["program"] = array[0]
                if array[1] == "RUNNING":
                    d["status"] = "1"
                    d["pid"] = array[3][:-1]
                else:
                    d["status"] = "0"
                    d["pid"] = ""
                conf = self.__read_config(self.conf)
                d["path"] = ""
                if conf:
                    for i in conf:
                        if d["program"] == i["program"]:
                            d["path"] = i["path"]
                            d["user"] = i["user"]
                            d["priority"] = i["priority"]
                array_list.append(d)
        res= public.ExecShell("supervisorctl update")
        return array_list 
  
    # 获取用户列表  
    def GetUserList(self, get):
        if not os.path.isfile(self.user):
            os.system(r"touch {}".format(self.user))
        res = public.ExecShell("cat /etc/passwd > %s" % self.user)
        with open(self.user,"r") as fr:
            users = fr.readlines()
        fr.close()
        os.remove(self.user)
        
        user_list = [] 
        special = ["bin", "daemon", "adm", "lp", "shutdown", "halt", "mail", "operator", "games", "avahi-autoipd", "systemd-bus-proxy", "systemd-network", "dbus", "polkitd", "tss", "ntp"]
        for u in users:
            user = re.split(':', u)[0]
            if user in special:
                continue
            user_list.append(user)
        return user_list
  
    def AddProcess(self, get):
        if not os.path.exists(self.profile):
            os.makedirs(self.profile)  
        if not os.path.exists(self.log):
            os.makedirs(self.log)
       
        program = get.pjname
        user = get.user
        rfile = get.rfile
        param = get.param
        command = rfile + " " + param
        # command = "/usr/bin/python /www/wwwroot/study_test/Main.py"
        projectfile = self.profile + program + ".ini"
        
        if not program:
            return public.ReturnMsg(False,'请输入管理进程的名称!')
        resComm = rfile.split(" ")[-1]
        if not os.path.isfile(resComm):
            return public.ReturnMsg(False,'请输入正确的执行文件!')
        if not os.access(resComm, os.X_OK): 
            return public.ReturnMsg(False,'文件不可执行!')
    
        w_body = ""
        w_body += "[program:" + program + "]" + "\n"
        w_body += "command=" + command + "\n" 
        w_body += "autorestart=true" + "\n"
        w_body += "stdout_logfile=" + self.log + program+ ".out.log" + "\n"
        # w_body += "stderr_logfile=" + self.log + "err.log" + "\n"
        w_body += "redirect_stderr=true" + "\n"   
        w_body += "user=" + user + "\n" 
        w_body += "priority=999"
  
        dir_or_files = os.listdir(self.profile)
        files = []
        for file in dir_or_files:
            if os.path.isfile(self.profile + file):
                files.append(file)
        if files:
            if program + ".ini" in files:
                return public.ReturnMsg(False,'该进程名已被使用!')

        res1 = public.ExecShell("ps -axj")
        if res1:
            for r in res1:
                if command in r or rfile in r:
                    return public.ReturnMsg(False,'该进程已被守护!')
        
        # 进程信息写入ini文件
        result = public.WriteFile(projectfile,w_body,mode='w+')
        if result:
            result1 = public.ExecShell("supervisorctl update")
            time.sleep(1.5)
            res1 = public.ExecShell("ps -axj")
            if res1:
                for r in res1:
                    if command in r or rfile in r:
                        # 进程信息写入config.json文件
                        d = dict()
                        d["program"] = program
                        d["command"] = command
                        d["user"] = user
                        d["path"] = resComm
                        d["priority"]="999"
                        conf = self.__read_config(self.conf)
                        conf.append(d)
                        ress = self.__write_config(self.conf, conf)
                        return public.ReturnMsg(True,'增加守护进程成功!')
                    else:
                        exe1 = command+";"+"echo $?"
                        res2 = public.ExecShell(exe1)    
                        os.remove(projectfile)
                        logpath = self.log + program + ".out.log"
                        if os.path.isfile(logpath):
                            os.remove(logpath)
                        if res2[1]=="":
                            return public.ReturnMsg(False,'增加守护进程失败!,文件执行结束太快!')        
                        public.ExecShell("supervisorctl update")
                        return public.ReturnMsg(False,'增加守护进程失败!,请输入正确执行命令!')  
  
    def RemoveProcess(self, get):
        name = get.program
        result = public.ExecShell("supervisorctl stop "+ name)
        program= self.profile + name + ".ini"
  
        # 删除config.json文件里的进程信息
        conf = self.__read_config(self.conf)
        for i in conf:
            if name == i["program"]:
                conf.remove(i)
        ress = self.__write_config(self.conf, conf)
        
        # 删除日志文件
        logpath = self.log + name + ".out.log"
        if os.path.isfile(logpath):
            os.remove(logpath)
  
         # 删除ini文件
        if os.path.isfile(program):
            os.remove(program)
            result = public.ExecShell("supervisorctl update")
            time.sleep(1)
            return public.ReturnMsg(True,'删除守护进程成功!')
        else:
            result = public.ExecShell("supervisorctl update")
            time.sleep(1)
            return public.ReturnMsg(False,'该守护进程不存在!')
  
    def UpdateProcess(self,get):
        oldname = get.pjname
        priority = get.level
        user = get.user
        # 修改config.json文件
        conf = self.__read_config(self.conf)
        d = dict()
        for i in conf:
            if oldname == i["program"]:
                d = i
                conf.remove(i)
                d["priority"] = priority
                d["user"] = user
                conf.append(d)
                break
        ress = self.__write_config(self.conf, conf)
        # 修改ini文件
        profile = self.profile + oldname + ".ini" 
        with open(profile,"r") as fr:
            lines = fr.readlines()
        content = "" 
        for i in lines:
            if re.match('user=.*', i):
                content += "user="+ user + "\n"
            elif re.match('priority=.*', i):
                content += "priority="+ priority + "\n"
            else:
                content += i  
        with open(profile,"r+") as f:
            read_data = f.read()
            f.seek(0)
            f.truncate() 
            f.write(content)
        result = public.ExecShell("supervisorctl update")
        time.sleep(1)
        return public.ReturnMsg(True,'修改守护进程成功!')
  
    def StartProcess(self, get):
        name = get.program
        res = self.Check_name(name)
        if res:
            result = public.ExecShell("supervisorctl start "+ name) 
            if "ERROR" in result[0]:
                return public.ReturnMsg(False,'项目已经启动!')
            return public.ReturnMsg(True,'启动成功!')
        else:
            res= public.ExecShell("supervisorctl update")
            time.sleep(1)
            return public.ReturnMsg(False,'该守护进程不存在!')
  
    def StopProcess(self, get):
        name = get.program
        res = self.Check_name(name)
        if res:
            result = public.ExecShell("supervisorctl stop "+ name)       
            if "ERROR" in result[0]:
                return public.ReturnMsg(False,'项目已经停止!')
            return public.ReturnMsg(True,'停止成功!')
        else:
            res= public.ExecShell("supervisorctl update")
            time.sleep(1)
            return public.ReturnMsg(False,'该守护进程不存在!')
  
    def GetProgressInfo(self, get):    
        name = get.program
        info = dict()
        conf = self.__read_config(self.conf)
        for i in conf:
            if name == i["program"]:
                info["daemoninfo"] = i
        userlist = self.GetUserList({})
        info["userlist"] = userlist
        return info
  
    def Check_name(self, name):    
        profile = self.profile + name + ".ini" 
        if os.path.isfile(profile):
            return True
        else:
            return False  
  
    # 读守护进程日志
    def GetProjectLog(self, get):
        name = get.pjname
        log_path = self.log + name + ".out.log"
        if os.path.exists(log_path):
            #f_body = public.ReadFile(logpath,mode='r')
            #return json.dumps(f_body)
            result = public.ExecShell("tail -n 800 %s" % log_path)[0]
            return result
        else:
            return "该项目没有日志" 
  
    # 读日志(终端)
    def GetTerminalLog(self, get):
        if os.path.exists(self.logpath):
            result = public.ExecShell("tail -n 800 %s" % self.logpath)[0]
            return result
        else:
            return "" 
    
    # 写日志(终端)
    def WriteLog(self, msg):
        #localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if not os.path.isfile(self.logpath):
            os.system(r"touch {}".format(self.logpath))
        #public.writeFile(self.logpath, localtime + "\n" + msg + "\n", "a+")
        public.writeFile(self.logpath, msg+ "\n", "a+")

    # 读取supervisord.conf文件配置
    def GetSupervisorFile(self,get):
        import files
        f = files.files()
        return f.GetFileBody(get)

    # 保存supervisord.conf文件配置
    def SaveSupervisorFile(self,get):
        import files
        f = files.files()
        return f.SaveFileBody(get)
  
    # 读config.json配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: 
            upBody = '[]'
        return json.loads(upBody)

    # 写config.json配置
    def __write_config(self ,path, data):
        return public.writeFile(path, json.dumps(data))            
                             