#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板网站备份工具 TO FTP
#-----------------------------
import sys,os,re
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel');
sys.path.insert(0,"class/")
import public,db,time,socket

class ftp_main:
    __setupPath = 'plugin/ftp'
    __path = '/';
    __exclude = ""
    
    def __init__(self):
        self.__path = self.GetConfig(None)[3];
        self.get_exclode()
    
    def GetConfig(self,get):
        path = self.__setupPath + '/config.conf';
        if not os.path.exists(path):
            if os.path.exists('conf/ftpAs.conf'): public.writeFile(path,public.readFile('conf/ftpAs.conf'));
        if not os.path.exists(path): return ['','','','/'];
        conf = public.readFile(path);
        if not conf: return ['','','','/'];
        return conf.split('|');
    
    def SetConfig(self,get):
        path = self.__setupPath + '/config.conf';
        conf = get.ftp_host + '|' + get.ftp_user +'|' + get.ftp_pass + '|' + get.ftp_path;
        public.writeFile(path,conf);
        return public.returnMsg(True,'设置成功!');
    
    def backupSite(self,name,count):
        sql = db.Sql();
        path = sql.table('sites').where('name=?',(name,)).getField('path');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = "网站["+name+"]不存在!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/site';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);
        
        filename= backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.tar.gz'
        public.ExecShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "'" + self.__exclude + " > /dev/null")
        
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        
        if not os.path.exists(filename):
            log = "网站["+name+"]备份失败!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        #上传到FTP
        self.updateFtp(filename);
        
        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?',(name,)).getField('id');
        sql.table('backup').add('type,name,pid,filename,addtime,size',('0',os.path.basename(filename),pid,'ftp',endDate,os.path.getsize(filename)))
        log = "网站["+name+"]备份到FTP成功,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog('计划任务',log)
        print("★["+endDate+"] " + log)
        print("|---保留最新的["+count+"]份备份")
        print("|---文件名:"+os.path.basename(filename))
        if self.__exclude: print(u"|---排除规则: " + self.__exclude)
        
        os.system('rm -f ' + filename);
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=? and filename=?',('0',pid,'ftp')).field('id,name,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename']);
                filename = (self.__path + '/' +backup['name']).replace('//','/')
                self.deleteFtp(filename);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break;
    
    def backupDatabase(self,name,count):
        sql = db.Sql();
        path = sql.table('databases').where('name=?',(name,)).getField('id');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = "数据库["+name+"]不存在!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/database';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);
        
        filename = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime())+".sql.gz"
        
        import re
        mysql_root = sql.table('config').where("id=?",(1,)).getField('mysql_root')
        mycnf = public.readFile('/etc/my.cnf');
        rep = "\[mysqldump\]\nuser=root"
        sea = '[mysqldump]\n'
        subStr = sea + "user=root\npassword=" + mysql_root+"\n";
        mycnf = mycnf.replace(sea,subStr)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf',mycnf);
        
        public.ExecShell("/www/server/mysql/bin/mysqldump --default-character-set="+ self.get_database_character(name) +" --force --opt " + name + " | gzip > " + filename)
        
        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = "数据库["+name+"]备份失败!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        mycnf = public.readFile('/etc/my.cnf');
        mycnf = mycnf.replace(subStr,sea)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf',mycnf);
        
        
        #上传到FTP
        self.updateFtp(filename);
        
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?',(name,)).getField('id');
        
        sql.table('backup').add('type,name,pid,filename,addtime,size',(1,os.path.basename(filename),pid,'ftp',endDate,os.path.getsize(filename)))
        log = "数据库["+name+"]备份成功,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog('计划任务',log)
        print("★["+endDate+"] " + log)
        print("|---保留最新的["+count+"]份备份")
        print("|---文件名:"+os.path.basename(filename))
        
        os.system('rm -f ' + filename);
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=? and filename=?',('1',pid,'ftp')).field('id,name,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename']);
                filename = (self.__path + '/' +backup['name']).replace('//','/')
                self.deleteFtp(filename);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break;
    
    #连接FTP
    def connentFtp(self):
        from ftplib import FTP
        path = self.__setupPath + '/config.conf';
        if not os.path.exists(path): path = 'data/ftpAs.conf';
        ftpAs = public.readFile(path);
        tmp = ftpAs.split('|');
        if tmp[0].find(':') == -1: tmp[0] += ':21';
        host = tmp[0].split(':');
        if host[1] == '': host[1] = '21'; 
        ftp=FTP() 
        ftp.set_debuglevel(0)
        ftp.connect(host[0],int(host[1]))
        ftp.login(tmp[1],tmp[2])
        if self.__path != '/':
            self.dirname = self.__path;
            self.path = '/'
            self.createDir(self,ftp)
        ftp.cwd(self.__path);
        return ftp;

        
    #创建目录
    def createDir(self,get,ftp = None):
        try:
            if not ftp: ftp = self.connentFtp();
            dirnames = get.dirname.split('/');
            ftp.cwd(get.path);
            for dirname in dirnames:
                if not dirname: continue;
                if not dirname in ftp.nlst(): ftp.mkd(dirname);
                ftp.cwd(dirname);
            return public.returnMsg(True,'目录创建成功!');
        except:
            return public.returnMsg(False,'目录创建失败!');
    
    #上传文件
    def updateFtp(self,filename):
        try:
            ftp = self.connentFtp();
            bufsize = 1024
            file_handler = open(filename,'rb')
            ftp.storbinary('STOR %s' % os.path.basename(filename),file_handler,bufsize)
            file_handler.close() 
            ftp.quit()
        except:
            if os.path.exists(filename): os.remove(filename)
            print('连接服务器失败!')
            return {'status':False,'msg':'连接服务器失败!'}
    
    #从FTP删除文件
    def deleteFtp(self,filename):
        try:
            ftp = self.connentFtp();
            try:
                ftp.rmd(filename);
            except:
                ftp.delete(filename);
            return True;
        except Exception as ex:
            print(ex)
            return False;
    
    #删除文件或目录
    def rmFile(self,get):
        self.__path = get.path;
        if self.deleteFtp(get.filename):
            return public.returnMsg(True,'删除成功!');
        return public.returnMsg(False,'删除失败!');
    
    #获取列表
    def getList(self,get = None):
        try:
            self.__path = get.path;
            ftp = self.connentFtp();
            result =  ftp.nlst();
            dirs = []
            files = []
            data = []
            for dt in result:
                if dt == '.' or dt == '..': continue;
                sfind = public.M('backup').where('name=?',(dt,)).field('size,addtime').find();
                if not sfind:
                    sfind = {}
                    sfind['addtime'] = '1970/01/01 00:00:01'
                tmp = {}
                tmp['name'] = dt
                tmp['time'] = int(time.mktime(time.strptime(sfind['addtime'],'%Y/%m/%d %H:%M:%S')))
                try:
                    tmp['size'] = ftp.size(dt);
                    tmp['dir'] = False;
                    tmp['download'] = self.getFile(dt);
                    files.append(tmp)
                except:
                    tmp['size'] = 0;
                    tmp['dir'] = True;
                    tmp['download'] = '';
                    dirs.append(tmp);
                    
            data = dirs + files;
            mlist = {}
            mlist['path'] = self.__path;
            mlist['list'] = data;
            return mlist;
        except Exception as ex:
            return {'status':False,'msg':str(ex)}
    
    #获取文件地址
    def getFile(self,filename):
        path = self.__setupPath + '/config.conf';
        ftpAs = public.readFile(path);
        tmp = ftpAs.split('|');
        if tmp[0].find(':') == -1: tmp[0] += ':21';
        host = tmp[0].split(':');
        if host[1] == '': host[1] = '21';
        return 'ftp://'+ tmp[1]+ ':'+ tmp[2] + '@' +  host[0] + ':' + host[1] + (self.__path + '/' + filename).replace('//','/');

    #获取文件地址2
    def download_file(self,filename):
        return self.getFile(filename)


    #备份指定目录
    def backupPath(self,path,count):
        sql = db.Sql();
        startTime = time.time();
        if path[-1:] == '/': path = path[:-1]
        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/path';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        filename= backup_path + "/Path_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.tar.gz'
        os.system("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "'" + self.__exclude + " > /dev/null")
                
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not os.path.exists(filename):
            log = u"目录["+path+"]备份失败"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        #上传文件
        if backup_path != '': backup_path += 'path/' + name + '/';
        self.updateFtp(filename);
        outTime = time.time() - startTime
        sql.table('backup').add('type,name,pid,filename,addtime,size',('2',path,'0',filename,endDate,os.path.getsize(filename)))
        log = u"目录["+path+"]备份成功,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog(u'计划任务',log)
        print(u"★["+endDate+"] " + log)
        print(u"|---保留最新的["+count+u"]份备份")
        print(u"|---文件名:"+filename)
        if self.__exclude: print(u"|---排除规则: " + self.__exclude)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and name=? and pid=?',('2',path,0)).field('id,filename').select();
        
        #清理本地文件
        if os.path.exists(filename): os.remove(filename)

        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']): os.remove(backup['filename'])
                filename = (self.__path + '/' + os.path.basename(backup['filename'])).replace('//','/')
                self.deleteFtp(filename);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print(u"|---已清理过期备份文件：" + backup['filename'])
                if num < 1: break;
        
    
    def backupSiteAll(self,save):
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backupSite(site['name'],save)
        

    def backupDatabaseAll(self,save):
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backupDatabase(database['name'],save)
    
    def get_exclode(self):
        tmp_exclude = os.getenv('BT_EXCLUDE')
        if not tmp_exclude: return ""
        for ex in tmp_exclude.split(','):
            self.__exclude += " --exclude=\"" + ex + "\""
        self.__exclude += " "
        return self.__exclude
    
    #取数据库字符集
    def get_database_character(self,db_name):
        try:
            import panelMysql
            tmp = panelMysql.panelMysql().query("show create database `%s`" % db_name.strip())
            return str(re.findall("SET\s+(.+)\s",tmp[0][1])[0])
        except:
            return 'utf8'
    


if __name__ == "__main__":
    import json
    data = None
    backup = ftp_main()
    type = sys.argv[1];
    if type == 'site':
        if sys.argv[2] == 'ALL':
             data = backup.backupSiteAll( sys.argv[3])
        else:
            data = backup.backupSite(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            data = backup.backupDatabaseAll(sys.argv[3])
        else:
            data = backup.backupDatabase(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'path':
        data = backup.backupPath(sys.argv[2],sys.argv[3])
        exit()
    elif type == 'list':
        data = backup.getList()
    elif type == 'download':
        data = backup.getFile(sys.argv[2]);
    