#!/usr/bin/python
# coding: utf-8
# +--------------------------------------------------------------------
# |   微擎助手 for 宝塔
# +-------------------------------------------------------------------
# |   Author: 超人
# +--------------------------------------------------------------------
import sys, os, json
os.chdir("/www/server/panel")
sys.path.append("class/")
import public

if __name__ != '__main__':
    from BTPanel import cache, session

class w7assistant_main:
    __plugin_path = "/www/server/panel/plugin/w7assistant/"
    __config = None
    __safe_mode_dir = 'attachment|data|framework'

    def __init__(self):
        pass

    def get_sites(self, args):
        sites = public.M('sites').field('id,name,edate,path,status').order('id desc').select()
        for site in sites:
            site['_is_w7'] = self._is_w7(site['path'])
            site['_safe_mode'] = self._get_safe_mode(site)
        sites.sort(None, None, True)
        return {'errno': 0, 'errmsg': 'ok', 'data': sites}

    def get_site_modules(self, args):
        import panelMysql
        import re

        site = public.M('sites').where('id=?', (args.siteid,)).field('id,name,edate,path,status').find()
        if not site:
            return {'errno': -1, 'errmsg': '非法请求！'}

        # 判断是否微擎站点
        if not self._is_w7(site['path']):
            return {'errno': -1, 'errmsg': '该站点不是微擎系统！'}

        # 获取密码加密参数：authkey
        filename = site['path'] + '/data/config.php'
        config = public.ReadFile(filename, 'r')
        if not config:
            return {'errno': -1, 'errmsg': '未找到系统配置文件: ' + filename}

        # 获取数据库名称
        dbname = public.M('databases').where('pid=?', (args.siteid)).getField('name')
        if not dbname:
            matches = re.search(u'\$config\[\'db\'\]\[\'master\'\]\[\'database\'\] = \'(\w*)\'', config, re.I);
            if not matches:
                return {'errno': -1, 'errmsg': '数据库名称未找到！'}
            dbname = matches.group(1)

        db = panelMysql.panelMysql()

        web_server = public.GetWebServer()
        file = public.GetConfigValue('setup_path')+'/panel/vhost/'+web_server+'/' + site['name'] + '.conf'
        conf = public.readFile(file)

        data = []
        # 获取应用数据
        sql = 'SELECT `name`,`title` FROM `' + dbname + '`.`ims_modules` WHERE `issystem`=0'
        modules = db.query(sql)
        if modules:
            for m in modules:
                status = 0
                matches = re.search(u''+m[0], conf, re.I)
                if matches:status = 1
                data.append({
                    'name': m[0],
                    'title': m[1],
                    'status': status,
                })
        return {'errno': 0, 'errmsg': 'ok', 'data': data}

    def get_php_info(self, args):
        import re, common, ajax
        a = ajax.ajax()

        # 获取微擎站点
        w7_sites = self._get_w7_sites()

        # 获取php版本
        data = {}
        web_server = public.GetWebServer()
        for site in w7_sites:
            conf = public.readFile(public.GetConfigValue('setup_path')+'/panel/vhost/'+web_server+'/'+site['name']+'.conf')
            if web_server == 'nginx':
                rep = "enable-php-([0-9]{2,3})\.conf"
            else:
                rep = "php-cgi-([0-9]{2,3})\.sock"
            matches = re.search(rep,conf).groups()
            if matches:
                php_version = matches[0]
                if php_version not in data:
                    get = common.dict_obj()
                    get.version = php_version
                    config = a.GetPHPConfig(get)
                    memcached = 'allow_install'
                    redis = 'allow_install'
                    opcache = 'allow_install'
                    if config['libs']:
                        for lib in config['libs']:
                            if lib['name'] == 'redis':
                                if lib['task'] == '0' and php_version in lib['phpversions']:
                                    redis = 'waiting_install'
                                elif lib['task'] == '-1' and php_version in lib['phpversions']:
                                    redis = 'installing'
                                elif lib['status']:
                                    redis = 'uninstall'
                            if lib['name'] == 'opcache':
                                if lib['task'] == '0' and php_version in lib['phpversions']:
                                    opcache = 'waiting_install'
                                elif lib['task'] == '-1' and php_version in lib['phpversions']:
                                    opcache = 'installing'
                                elif lib['status']:
                                    opcache = 'uninstall'
                    data[php_version] = {
                        'names': [],
                        'php_ext': {
                            'redis': redis,
                            'opcache': opcache,
                        },
                        'php_version': php_version,
                        '_php_version': php_version[0:1]+'.'+php_version[-1]
                    }
                data[php_version]['names'].append(site['name'])
        return {'errno': 0, 'errmsg': 'ok', 'data': data}

    def set_php_ext(self, args):
        import common,db,time,re

        if args.status == 'open':
            # 安装扩展
            path = public.GetConfigValue('setup_path') + '/php'
            if not os.path.exists(path): os.system("mkdir -p " + path);
            get = common.dict_obj()
            get.name = args.php_ext
            get.version = args.php_version
            get.type = '1'
            if session['server_os']['x'] != 'RHEL': get.type = '3'
            apacheVersion = 'false';
            if public.get_webserver() == 'apache':
                apacheVersion = public.readFile(public.GetConfigValue('setup_path')+'/apache/version.pl');
            public.writeFile('/var/bt_apacheVersion.pl',apacheVersion)
            public.writeFile('/var/bt_setupPath.conf',public.GetConfigValue('root_path'))
            isTask = '/tmp/panelTask.pl'
            execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh " + str(get.type) + " install " + str(get.name) + " "+ str(get.version);
            sql = db.Sql()
            if hasattr(get,'id'):
                id = get.id;
            else:
                id = None;
            sql.table('tasks').add('id,name,type,status,addtime,execstr',(None,'安装['+get.name+'-'+get.version+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
            public.writeFile(isTask,'True')
            msg = '添加安装任务['+get.name+'-'+get.version+']成功'
            public.WriteLog('微擎助手', msg);
            time.sleep(0.1);

            # 开启微擎缓存
            if args.php_ext == 'redis':
                # 获取微擎站点
                w7_sites = self._get_w7_sites()
                for site in w7_sites:
                    filename = site['path'] + '/data/config.php'
                    config = public.ReadFile(filename, 'r')
                    matches = re.search(u'\$config\[\'setting\'\]\[\'cache\'\] = \'(\w*)\'', config, re.I)
                    if matches:
                        # mysql || memcache
                        cache = matches.group(1)
                        if cache != 'redis':
                            regex = re.compile(u'\$config\[\'setting\'\]\[\'cache\'\] = \'(\w*)\'')
                            config = regex.sub(u'$config[\'setting\'][\'cache\'] = \'redis\'', config)

                            # 检查redis参数
                            if not re.search(u'\$config\[\'setting\'\]\[\'redis\'\](.*)', config, re.I):
                                config += '''
$config['setting']['redis']['server'] = '127.0.0.1';
$config['setting']['redis']['port'] = 6379;
$config['setting']['redis']['pconnect'] = 0;
$config['setting']['redis']['requirepass'] = '';
$config['setting']['redis']['timeout'] = 1;
$config['setting']['redis']['session'] = 1;
'''
                            public.writeFile(filename, config)
            return {'errno': 0, 'errmsg': msg}
        else:
            # 卸载扩展
            public.writeFile('/var/bt_setupPath.conf', public.GetConfigValue('root_path'))
            get = common.dict_obj()
            get.name = args.php_ext
            get.version = args.php_version
            get.type = '0'
            if session['server_os']['x'] != 'RHEL': get.type = '3'
            execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/install && /bin/bash install_soft.sh "+str(get.type)+" uninstall " + get.name.lower() + " "+ get.version.replace('.','')
            os.system(execstr)
            msg = '关闭['+get.name+'-'+str(get.version)+']成功'
            public.WriteLog('微擎助手', msg)
            return {'errno': 0, 'errmsg': msg}

    def reset_password(self, args):
        import panelMysql
        import hashlib
        import re

        site = public.M('sites').where('id=?', (args.siteid,)).field('id,name,edate,path,status').find()
        if not site:
            return {'errno': -1, 'errmsg': '非法请求！'}

        # 判断是否微擎站点
        if not self._is_w7(site['path']):
            return {'errno': -1, 'errmsg': '该站点不是微擎系统！'}

        # 获取密码加密参数：authkey
        filename = site['path'] + '/data/config.php'
        config = public.ReadFile(filename, 'r')
        if not config:
            return {'errno': -1, 'errmsg': '未找到系统配置文件: ' + filename}
        matches = re.search(u'\$config\[\'setting\'\]\[\'authkey\'\] = \'(\w*)\'', config, re.I)
        if not matches:
            return {'errno': -1, 'errmsg': '微擎配置文件中authkey未找到！'}
        authkey = matches.group(1)

        # 获取数据库名称
        dbname = public.M('databases').where('pid=?', (args.siteid)).getField('name')
        if not dbname:
            matches = re.search(u'\$config\[\'db\'\]\[\'master\'\]\[\'database\'\] = \'(\w*)\'', config, re.I);
            if not matches:
                return {'errno': -1, 'errmsg': '数据库名称未找到！'}
            dbname = matches.group(1)

        db = panelMysql.panelMysql()

        # 检查账号是否存在
        sql = 'SELECT `uid` FROM `' + dbname + '`.`ims_users` WHERE `username`=\'' + args.username + '\''
        user = db.query(sql)
        if not user:
            return {'errno': -1, 'errmsg': '用户名不存在！'}

        # 计算新密码hash
        salt = public.GetRandomString(8)
        password = hashlib.sha1(args.password + '-' + salt + '-' + authkey).hexdigest()

        # 更新密码
        sql = 'UPDATE `' + dbname + '`.`ims_users` SET `password`=\'' + password + '\', `salt`=\'' + salt + '\' WHERE `username`=\'' + args.username + '\''
        db.execute(sql)

        # 记录日志
        public.WriteLog('微擎助手', '重置密码：网站['+site['name']+']密码重置成功')
        return {'errno': 0, 'errmsg': 'ok'}

    def safety_reinforce(self, args):
        import re

        site = public.M('sites').where('id=?', (args.siteid,)).field('id,name,edate,path,status').find()
        if not site:
            return {'errno': -1, 'errmsg': '非法请求！'}

        # 判断是否微擎站点
        if not self._is_w7(site['path']):
            return {'errno': -1, 'errmsg': '该站点不是微擎系统！'}

        module_name = '__W7ASSISTANT_SUPERMAN__'
        if args.module_name and args.mode == '2':
            module_name = args.module_name

        # webserver配置规则
        web_server = public.GetWebServer()
        if web_server == 'nginx':
            rule = '''
    #W7ASSISTANT-START-MODE%(MODE)s
    location ~ ^/(%(DIR)s)/.*\.(php|php5)$ {
        deny all;
    }''' % {'MODE': args.mode, 'DIR': self.__safe_mode_dir}
            if args.module_name and args.mode == '2':
                rule += '''
    location ~ ^/addons/(?:(?!(%(MODULE_NAME)s)).)*/.*\.(php|php5)$ {
        deny all;
    }''' % {'MODULE_NAME': module_name}
            rule += '''
    #W7ASSISTANT-END'''
        else:
            rule = '''
    #W7ASSISTANT-START-MODE%(MODE)s
    <Directory ~ "^%(PATH)s/(%(DIR)s)">
        <FilesMatch "\.(php|php5)$">
            Order allow,deny
            Deny from all
        </FilesMatch>
    </Directory>
    #W7ASSISTANT-END''' % {'MODE': args.mode, 'PATH': site['path'], 'DIR': self.__safe_mode_dir}

        # 更新站点配置文件
        file = public.GetConfigValue('setup_path')+'/panel/vhost/'+web_server+'/' + site['name'] + '.conf'
        conf = public.readFile(file)
        if conf:
            if args.act == 'close':
                action_title = '关闭'
                regex = re.compile(u'(\s\s\s\s)#W7ASSISTANT-START([\s\S]*)#W7ASSISTANT-END\n(\s*)\n')
                conf = regex.sub(u'', conf)
                public.writeFile(file, conf)
                #清理webserver转换时生成的rewrite文件（会导致关闭防护失效）
                rewrite_file = public.GetConfigValue('setup_path')+'/panel/vhost/rewrite/' + site['name'] + '.conf'
                rewrite_conf = public.readFile(rewrite_file)
                if rewrite_conf:
                    matches = re.search(u'data\|attachment', rewrite_conf)
                    if matches:
                        regex = re.compile(u'rewrite \^/\(data\|attachment(.*);\n')
                        rewrite_conf = regex.sub(u'', rewrite_conf)
                        public.writeFile(rewrite_file, rewrite_conf)
            elif args.act == 'open':
                action_title = '开启'
                matches = re.search(u'#W7ASSISTANT-START', conf)
                if matches:
                    # 已开启时先关闭
                    regex = re.compile(u'(\s\s\s\s)#W7ASSISTANT-START([\s\S]*)#W7ASSISTANT-END\n(\s*)\n')
                    conf = regex.sub(u'', conf)
                if web_server == 'nginx':
                    # 站点配置文件路径和数据库保存的路径存在差异
                    str = 'root '+site['path']
                    if site['path'][-1] != '/':
                        str += '/'
                    str += ';'
                else:
                    str = '</FilesMatch>'
                conf = re.sub(str, str+"\n"+rule, conf)
                public.writeFile(file, conf)

        # 重载配置文件
        public.ServiceReload()

        # 记录日志
        if args.mode == '2':
            mode_title = '严格模式'
        else:
            mode_title = '宽松模式'
        public.WriteLog('微擎助手', '安全加固：网站['+site['name']+'-'+action_title+mode_title+']')
        return {'errno': 0, 'errmsg': 'ok'}

    def get_rollback_data(self, args):
        import time

        site = public.M('sites').where('id=?', (args.siteid,)).field('id,name,edate,path,status').find()
        if not site:
            return {'errno': -1, 'errmsg': '非法请求！'}

        # 获取更新目录
        backup_path = site['path'] + '/data/patch/backup'
        dirs = os.listdir(backup_path)

        # 获取更新文件
        result = []
        if dirs:
            # 降序排序
            dirs.sort(None, None, True)
            for dir_name in dirs:
                sub_dirs = os.listdir(backup_path+'/'+dir_name)
                if sub_dirs:
                    for backid in sub_dirs:
                        # 更新文件数
                        files_count = -1
                        path = backup_path+'/'+dir_name+'/'+backid
                        content = public.readFile(path+'/map.json')
                        if content:
                            files_arr = json.loads(content)
                            files_count = len(files_arr)

                        # 目录创建时间
                        createtime = os.path.getctime(path)

                        result.append({
                            'name': dir_name,
                            'date': dir_name[0:4] + '-' + dir_name[4:6] + '-' + dir_name[-2:],
                            'backid': backid,
                            'time': time.strftime('%H:%M:%S', time.localtime(createtime)),
                            'files_count': files_count,
                            'files': files_arr,
                        })
        return {'errno': 0, 'errmsg': 'ok', 'data': result}

    def do_rollback(self, args):
        site = public.M('sites').where('id=?', (args.siteid,)).field('id,name,edate,path,status').find()
        if not site:
            return {'errno': -1, 'errmsg': '非法请求！'}

        src = site['path']+'/data/patch/backup/'+args.backpath
        if not os.path.isdir(src):
            return {'errno': -1, 'errmsg': '源目录('+src+')不存在！'}

        dst = site['path']
        if not os.path.isdir(dst):
            return {'errno': -1, 'errmsg': '目标目录('+dst+')不存在！'}

        # 拷贝目录（覆盖）
        command = 'cp -prf '+src+'/* '+dst
        public.ExecShell(command)

        # 记录日志
        public.WriteLog('微擎助手', '升级回滚：网站['+site['name']+']回滚到['+args.backpath+']')
        return {'errno': 0, 'errmsg': 'ok'}

    def _is_w7(self, path):
        import re
        filename = path + '/framework/bootstrap.inc.php'
        content = public.ReadFile(filename, 'r')
        if not content:
            return False
        matches = re.search(u'WeEngine|define\(\'IN_IA\', True\);', content, re.M | re.I)
        if not matches:
            return False
        return True

    def _get_safe_mode(self, site):
        import re

        web_server = public.GetWebServer()
        file = public.GetConfigValue('setup_path')+'/panel/vhost/'+web_server+'/' + site['name'] + '.conf'
        conf = public.readFile(file)
        if conf:
            matches = re.search(u'#W7ASSISTANT-START-MODE2', conf)
            if matches:
                return 2
            matches = re.search(u'#W7ASSISTANT-START-MODE1', conf)
            if matches:
                return 1
        return 0

    def _get_w7_sites(self):
        w7_sites = []
        sites = public.M('sites').field('id,name,edate,path,status').order('id desc').select()
        for site in sites:
            is_w7 = self._is_w7(site['path'])
            if is_w7:
                w7_sites.append(site)
        return w7_sites