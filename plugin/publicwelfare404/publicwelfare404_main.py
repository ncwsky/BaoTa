#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: Sudem <sang8052@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   404公益
#+--------------------------------------------------------------------
import sys,os,json,base64,requests,psutil

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
class publicwelfare404_main:

    __plugin_path = "/www/server/panel/plugin/publicwelfare404/"
    __config = None


    #构造方法
    def  __init__(self):
        if not os.path.exists(self.__plugin_path+"conf/sys.json"):
            #插件尚未初始化
            #初始化插件
            self.sys_init()


    #插件初始化函数
    #生成config 文件 写入当前运行状态，和404页面的风格
    def sys_init(self):
         config={"status":"off"}
         os.mkdir(self.__plugin_path+"conf/")
         os.mkdir(self.__plugin_path + "conf/site/")
         public.WriteFile(self.__plugin_path+"conf/sys.json",json.dumps(config))


   #取得某个网站的配置信息
    def site_info(self,args):
        path = public.M('sites').where('name=?',(args.site,)).getField('path')
        if not os.path.exists(self.__plugin_path + "conf/site/" + args.site + ".json"):
            status="off"
            demoid="-1"
            demourl=""
        else:
            status="on"
            data=json.loads(public.readFile(self.__plugin_path + "conf/site/" + args.site + ".json"))
            demoid=data['demoid']
            demourl=data['demourl']
        return {"status": status, "path": path, "demoid": demoid, "demourl": demourl}

    #将网站设置成404站点
    def site_install(self,args):
        sites = []
        if args.site == "all":
            site = {"name": "all", "path": "all", "demoid": args.demoid, "demourl": args.demourl}
            public.WriteFile(self.__plugin_path + "conf/site/" + site['name'] + ".json", json.dumps(site))
            data = public.M('sites').field('name,path').order('id desc').select()
            #设置所有站点为404站点
            for _data in data:
                site = {"name": _data['name'], "path": _data['path'], "demoid": args.demoid, "demourl": args.demourl}
                sites.append(site)
        else:
            path = public.M('sites').where('name=?', (args.site,)).getField('path')
            site = {"name": args.site, "path": path, "demoid": args.demoid, "demourl": args.demourl}
            sites.append(site)
        for site in sites:
            if not os.path.exists(site['path']+"/404.html.back"):
                 #备份原有文件
                 os.popen("cp "+site['path']+"/404.html "+site['path']+"/404.html.back")
            #下载新的文件
            _demo=requests.get(site['demourl'], verify=False)
            _demo.encoding="utf-8"
            demo= _demo.text
            public.WriteFile(site['path']+"/404.html",demo)
            #启用404 功能
            #修改Nginx 的配置文件
            nginx=public.readFile("/www/server/panel/vhost/nginx/"+site['name']+".conf")
            nginx = nginx.replace("#error_page 404 /404.html;", "error_page 404 /404.html;")
            public.WriteFile("/www/server/panel/vhost/nginx/"+site['name']+".conf",nginx)
            #修改Apache的配置文件
            apache=public.readFile("/www/server/panel/vhost/apache/"+site['name']+".conf")
            apache=apache.replace("#errorDocument 404 /404.html", "errorDocument 404 /404.html")
            public.WriteFile("/www/server/panel/vhost/apache/" + site['name'] + ".conf", apache)
            #写入404配置信息
            public.WriteFile(self.__plugin_path+"conf/site/"+site['name']+".json", json.dumps(site))
        return {"status": "success"}

    def site_uninstall(self,args):
        sites = []
        if args.site == "all":
            data = public.M('sites').field('name,path').order('id desc').select()
            os.popen("rm -rf " + self.__plugin_path + "conf/site/all.json")
            # 设置所有站点
            for _data in data:
                site = {"name": _data['name'], "path": _data['path']}
                sites.append(site)
        else:
            path = public.M('sites').where('name=?', (args.site,)).getField('path')
            site = {"name": args.site, "path": path}
            sites.append(site)
        for site in sites:
            #判断网站是否需要关闭
            if os.path.exists(self.__plugin_path+"conf/site/" + site['name'] + ".json"):
                # 还原备份的文件
                os.popen("mv " + site['path'] + "/404.html.back " + site['path'] + "/404.html")
                # 关闭404 功能
                # 修改Nginx 的配置文件
                nginx = public.readFile("/www/server/panel/vhost/nginx/" + site['name'] + ".conf")
                nginx = nginx.replace("error_page 404 /404.html;", "#error_page 404 /404.html;")
                public.WriteFile("/www/server/panel/vhost/nginx/" + site['name'] + ".conf", nginx)
                # 修改Apache的配置文件
                apache = public.readFile("/www/server/panel/vhost/apache/" + site['name'] + ".conf")
                apache = apache.replace("errorDocument 404 /404.html", "#errorDocument 404 /404.html")
                public.WriteFile("/www/server/panel/vhost/apache/" + site['name'] + ".conf", apache)
                # 删除404配置信息
                os.popen("rm -rf " + self.__plugin_path + "conf/site/" + site['name'] + ".json")

        return {"status": "success"}



   #连接宝塔数据库,获取所有指点的备注，站点名称信息
    def site_list(self,args):
        data = public.M('sites').field('name,ps').order('id desc').select()
        return {"status": "success", "num":len(data), "sites": data}









