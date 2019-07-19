#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 邹浩文 <627622230@qq.com>
# +-------------------------------------------------------------------

#-----------------------------
# 宝塔Linux面板网站备份工具 - google cloud storage
#-----------------------------
import sys,os,json
from google.cloud import storage
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public,db,time,re

class gcloud_storage_main:
    __setupPath = '/www/server/panel/plugin/gcloud_storage'
    __json = __setupPath + '/google.json'
    __bucket_name_file = __setupPath + "/bucket_name.conf"
    __bucket_name = None
    __get_conf_result = None

    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/www/server/panel/plugin/gcloud_storage/google.json"
        self.__get_conf_result = self.__get_config()
        self.__set_libList()

    def __get_config(self):
        if not os.path.exists(self.__json):
            return public.returnMsg(False, 'not_json') #显示获取json key教程
        self.__bucket_name = public.readFile(self.__bucket_name_file)
        if not self.__bucket_name:
            return public.returnMsg(False, 'not_bucket_name')  # 显示获取json key教程

    # 获取数据库编码
    def get_database_character(self,db_name):
        try:
            import panelMysql
            tmp = panelMysql.panelMysql().query("show create database `%s`" % db_name.strip())
            return str(re.findall("SET\s+(.+)\s", tmp[0][1])[0])
        except:
            return 'utf8'

    # 设置libList
    def __set_libList(self):
        libList = public.readFile("/www/server/panel/data/libList.conf")
        if libList:
            libList = json.loads(libList)
        for i in libList:
            if "google.cloud" in i.values():
                i["module"] = "os"
                public.writeFile("/www/server/panel/data/libList.conf", json.dumps(libList))
            if "google" in i.values():
                return
        d = {
	"name":"Google Cloud Storage",
	"type":"Cron job",
	"ps":"Back up your website or database to Google Cloud Storage.",
	"status":False,
	"opt":"gcloud",
	"module":"os",
	"script":"google",
	"help":"http://forum.aapanel.com",
	"key":"",
	"secret":"",
	"bucket":"",
	"domain":"",
	"check":["/www/server/panel/plugin/gcloud_storage/gcloud_storage_main.py","/www/server/panel/script/backup_gcloud.py"]
}
        d1 = {
	"name":"谷歌云存储",
	"type":"计划任务",
	"ps":"将网站或数据库打包备份到谷歌云存储.",
	"status":False,
	"opt":"gcloud",
	"module":"os",
	"script":"google",
	"help":"http://www.bt.cn/bbs",
	"key":"",
	"secret":"",
	"bucket":"",
	"domain":"",
	"check":["/www/server/panel/plugin/gcloud_storage/gcloud_storage_main.py","/www/server/panel/script/backup_gcloud.py"]
}
        language = public.readFile("/www/server/panel/config/config.json")
        if "English" in language:
            data = d
        else:
            data = d1
        libList.append(data)
        public.writeFile("/www/server/panel/data/libList.conf",json.dumps(libList))

    def set_bucket_name(self,get):
        rep = "[\-\_\.\w]+"
        if not re.search(rep,get.bucket_name):
            return public.returnMsg(False, 'bucket_name不合法，请确认后再试')
        public.writeFile(self.__bucket_name_file,str(get.bucket_name))
        return public.returnMsg(True, 'bucket_name添加成功')

    def set_google_json(self,get):
        data = json.loads(get.google_json)
        public.writeFile(self.__setupPath+"/google.json",json.dumps(data))
        return public.returnMsg(True, 'Google json 添加成功')

    def list_blobs_with_prefix(self, get):
        delimiter = "/"
        path = str(get.path)
        if self.__get_conf_result:
            return self.__get_conf_result
        if path and path[0] == "/":
            path = path[1:]
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.__bucket_name)
        blobs = bucket.list_blobs(prefix=path, delimiter="/")
        blob_list = []
        for blob in blobs:
            name = str(blob.name)
            if not name:
                continue
            if "/" in name:
                name = name.split("/")[-1]
            if not name:
                continue
            data = {}
            data["type"] = "F"
            data["download"] = None
            data["name"] = name
            data["size"] = blob.size
            data["time"] = str(blob.generation)[:-6]
            blob_list.append(data)
        if delimiter:
            for prefix in blobs.prefixes:
                prefix = prefix.split("/")[-2]+"/"
                blob_list.append({"name":prefix,"type":"D","time":None,"size":None,"download":None})
        if not path or path[0] != "/":
            path = "/" + path
        return {"path":path,"list":blob_list}

    def download_blob(self, get):
        source_file = get.source_blob_name
        if source_file[0] == "/":
            source_file = source_file[1:]
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.__bucket_name)
        blob = bucket.blob(source_file)
        blob.download_to_filename(get.destination_file_name)
        return public.returnMsg(True, '下载成功')

    def create_directory(self,get):
        directory = get.path
        if directory[0] == "/":
            directory = directory[1:]
        if directory[-1] != "/":
            directory += "/"
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.__bucket_name)
        blob = bucket.blob(directory)
        blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')
        return public.returnMsg(True, '创建成功')

    def __file_md5_hash(self,filename):
        import base64
        if not os.path.isfile(filename): return False;
        import hashlib
        my_hash = hashlib.md5()
        f = open(filename, 'rb')
        while True:
            b = f.read(8096)
            if not b:
                break
            my_hash.update(b)
        f.close()
        return base64.b64encode(my_hash.digest())

    def __get_md5(self,blob_name):
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.__bucket_name)
        blob = bucket.get_blob(blob_name)
        return blob.md5_hash


    def upload_file(self,get):
        if not os.path.exists(get.filename):
            return public.returnMsg(False, '上传失败，没有找到该文件 ' + get.filename)
        destination_blob_name = get.filename.split("/")[-1]
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.__bucket_name)
        blob = bucket.blob(get.path + destination_blob_name)
        blob.upload_from_filename(get.filename)
        localfile_md5hash = self.__file_md5_hash(get.filename)
        remotefile_md5hash = self.__get_md5(get.path + destination_blob_name)
        if localfile_md5hash == remotefile_md5hash:
            return public.returnMsg(True, '上传成功 '+get.filename)
        else:
            n = 0
            while n < 5:
                self.upload_file(get)

    def delete_blob(self, get):
        filename = get.filename
        if filename[0] == "/":
            filename = filename[1:]
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.__bucket_name)
        if filename[-1] == "/":
            blobs = bucket.list_blobs(prefix=filename)
            for blob in blobs:
                blob.delete()
        else:
            blob = bucket.blob(filename)
            blob.delete()
        return public.returnMsg(True, '删除成功 ' + filename)

        # 备份网站
    def backup_site(self, name, count):
        sql = db.Sql()
        path = sql.table('sites').where('name=?', (name,)).getField('path')
        startTime = time.time()
        if not path:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "网站[" + name + "]不存在!"
            print("★[" + endDate + "] " + log)
            print("----------------------------------------------------------------------------")
            return

        backup_path = sql.table('config').where("id=?", (1,)).getField('backup_path') + '/site'
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path)

        filename = backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',
                                                                      time.localtime()) + '_' + public.GetRandomString(
            8) + '.tar.gz'
        public.ExecShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(
            path) + "' > /dev/null")
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())

        if not os.path.exists(filename):
            log = "网站[" + name + "]备份失败!"
            print("★[" + endDate + "] " + log)
            print("----------------------------------------------------------------------------")
            return;

        # 上传文件
        get = getObject()
        get.filename = filename
        get.path = 'bt_backup/sites/' + name + "/"
        print("开始上传")

        self.upload_file(get)
        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?', (name,)).getField('id');
        download = get.path + '/' + os.path.basename(filename)
        sql.table('backup').add('type,name,pid,filename,addtime,size',('0', download, pid, 'gcloud_storage', endDate, os.path.getsize(filename)))
        log = "网站[" + name + "]已成功备份到谷歌云存储,用时[" + str(round(outTime, 2)) + "]秒"
        public.WriteLog('计划任务', log)
        print("★[" + endDate + "] " + log)
        print("|---保留最新的[" + count + "]份备份")
        print("|---文件名:" + os.path.basename(filename))

        # 清理本地文件
        public.ExecShell("rm -f " + filename)

        # 清理多余备份
        backups = sql.table('backup').where('type=? and pid=? and filename=?', ('0', pid, 'gcloud_storage')).field(
            'id,name,filename').select()
        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                print(backup['filename'])
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename'])
                get.filename = 'bt_backup/sites/' + name + '/' + backup['name'].split("/")[-1]
                try:
                    self.delete_blob(get)
                except Exception as e:
                    print(e)
                sql.table('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break
        return None

    # 备份数据库
    def backup_database(self, name, count):
        sql = db.Sql()
        path = sql.table('databases').where('name=?', (name,)).getField('id')
        startTime = time.time()
        if not path:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "数据库[" + name + "]不存在!"
            print("★[" + endDate + "] " + log)
            print("----------------------------------------------------------------------------")
            return;

        backup_path = sql.table('config').where("id=?", (1,)).getField('backup_path') + '/database'
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);

        filename = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',
                                                                     time.localtime()) + '_' + public.GetRandomString(
            8) + ".sql.gz"

        import re
        mysql_root = sql.table('config').where("id=?", (1,)).getField('mysql_root')
        mycnf = public.readFile('/etc/my.cnf')
        rep = "\[mysqldump\]\nuser=root"
        sea = "[mysqldump]\n"
        subStr = sea + "user=root\npassword=" + mysql_root + "\n"
        mycnf = mycnf.replace(sea, subStr)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf', mycnf)
        public.ExecShell(
            "/www/server/mysql/bin/mysqldump--default-character-set="+ self.get_database_character(name) +" --force --opt " + name + " | gzip > " + filename)
        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "数据库[" + name + "]备份失败!"
            print("★[" + endDate + "] " + log)
            print("---------------------------------------------------------------------------")
            return
        mycnf = public.readFile('/etc/my.cnf')
        mycnf = mycnf.replace(subStr, sea)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf', mycnf)
        # 上传
        get = getObject()
        get.filename = filename
        get.path = 'bt_backup/database/' + name + '/'
        print(filename)
        self.upload_file(get)
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?', (name,)).getField('id')
        download = get.path + '/' + os.path.basename(filename)
        sql.table('backup').add('type,name,pid,filename,addtime,size',(1, download, pid, 'gcloud_storage', endDate, os.path.getsize(filename)))
        log = "数据库[" + name + "]已成功备份到谷歌云存储,用时[" + str(round(outTime, 2)) + "]秒"
        public.WriteLog('计划任务', log)
        print("★[" + endDate + "] " + log)
        print("|---保留最新的[" + count + "]份备份")
        print("|---文件名:" + os.path.basename(filename))
        # 清理本地文件
        public.ExecShell("rm -f " + filename)
        # 清理多余备份
        backups = sql.table('backup').where('type=? and pid=? and filename=?', ('1', pid, 'gcloud_storage')).field(
            'id,name,filename').select()
        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename'])
                get.filename = 'bt_backup/database/' + name + '/' + backup['name'].split("/")[-1]
                try:
                    self.delete_blob(get)
                except Exception as e:
                    print(e)
                sql.table('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break
        return None

    # 备份指定目录
    def backup_path(self, path, count):
        sql = db.Sql()
        startTime = time.time()
        if path[-1:] == '/': path = path[:-1]
        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?", (1,)).getField('backup_path') + '/path'
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        filename = backup_path + "/Path_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',
                                                                       time.localtime()) + '.tar.gz'
        os.system("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(
            path) + "' > /dev/null")

        get = getObject()
        get.filename = filename
        get.path = 'bt_backup/path/' + name + "/"
        self.upload_file(get)

        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        if not os.path.exists(filename):
            log = u"目录[" + path + "]备份失败"
            print(u"★[" + endDate + "] " + log)
            print(u"----------------------------------------------------------------------------")
            return

        outTime = time.time() - startTime
        download = get.path + '/' + os.path.basename(filename)
        print(name)
        sql.table('backup').add('type,name,filename,addtime,size',('2', download, 'gcloud_storage', endDate, os.path.getsize(filename)))

        log = u"目录[" + path + "]备份成功,用时[" + str(round(outTime, 2)) + "]秒"
        public.WriteLog(u'计划任务', log)
        print(u"★[" + endDate + "] " + log)
        print(u"|---保留最新的[" + count + u"]份备份")
        print(u"|---文件名:" + filename)

        # 清理多余备份
        backups = sql.table('backup').where('type=? and filename=?',('2',"gcloud_storage")).field('id,name,filename').select()
        print(backups)
        # 清理本地备份
        if os.path.exists(filename): os.remove(filename)

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename'])
                get.filename = 'bt_backup/path/' + name + '/' + backup['name'].split("/")[-1]
                print(get.filename)
                try:
                    self.delete_blob(get)
                except Exception as e:
                    print(e)
                sql.table('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                print(u"|---已清理过期备份文件：" + backup['filename'])
                if num < 1: break
        return None

    def backup_all_site(self, save):
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backup_site(site['name'], save)

    def backup_all_databases(self, save):
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backup_database(database['name'], save)

class getObject:
    pass

if __name__ == "__main__":
    import json
    data = None
    q = gcloud_storage_main()
    type = sys.argv[1]
    if type == 'site':
        if sys.argv[2] == 'ALL':
             q.backup_all_site( sys.argv[3])
        else:
            q.backup_site(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            data = q.backup_all_databases(sys.argv[3])
        else:
            data = q.backup_database(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'path':
        data = q.backup_path(sys.argv[2],sys.argv[3])
    else:
        data = 'ERROR: 参数不正确!'
    print(json.dumps(data))