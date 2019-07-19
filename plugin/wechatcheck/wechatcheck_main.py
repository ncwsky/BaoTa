#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: monkeyapi <aiens@woji.net>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔第三方应用开发-微信域名检测
#+--------------------------------------------------------------------
import sys,os,json

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


class wechatcheck_main:
    __plugin_path = "/www/server/panel/plugin/wechatcheck/"
    __config = None

    #构造方法
    def  __init__(self):
        pass



    #获取面板域名列表
    #已登录面板的情况下访问sitelist方法：/plugin?action=a&name=wechatcheck&s=sitelist

    def sitelist(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 12
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)

        

        #获取当前页的数据列表
        if not 'url' in args:
            #取网站总行数
            count = public.M('sites').count()

            #获取分页数据
            page_data = public.get_page(count,args.p,args.rows,args.callback)
            site_list = public.M('sites').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,name,ps,addtime').select()
        else:
            site_list = [{'name': args.url}]

        #检测当前数据中的域名状态
        #
        #从本地配置获取appkey，如果没有，从云端获取appkey并存储
        appkey = self.__get_config('appkey')        
        if appkey is None:
            ip = public.GetLocalIp()
            #public.WriteLog('微信域名检测插件','[微信域名检测]通过IP获取appkey: '+ip)
            serv_r = public.HttpGet('http://api.bt.woji.net/?ip='+ip)
            #public.WriteLog('微信域名检测插件','[微信域名检测]获取远程appkey: '+serv_r)
            serv_dict = json.loads(serv_r)
            public.WriteLog('微信域名检测插件','[微信域名检测]获取远程appkey: '+serv_dict['appkey'])
            self.__set_config('appkey',serv_dict['appkey'])
            appkey = self.__get_config('appkey')
            #public.WriteLog('微信域名检测插件','[微信域名检测]获取本地appkey: '+appkey)
        #通过appkey请求云端获取数据
        #
        for sl_index in range(len(site_list)):
            monkeyapi_r  = public.HttpGet('http://api.bt.woji.net/?ip='+public.GetLocalIp()+'&appkey='+appkey+'&url='+site_list[sl_index]['name'])
            site_list[sl_index]['domainstatus'] = monkeyapi_r
        
        #返回数据到前端
        if not 'url' in args:
            return {'data': site_list,'page':page_data['page'] }
        else:
            return {'data': site_list,'page':'nopage' }
        
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

