#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 启安科技风控平台查询插件
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 启安科技 (https://www.qiansec.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 启安科技 <791343541@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   启安科技风控平台查询插件
#+--------------------------------------------------------------------
import sys,os,json,re
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


class qiankeji_main:
    __plugin_path = "/www/server/panel/plugin/qiankeji/"
    __APIURL = 'http://116.62.246.63:8080/api.php'
    __config = None
    __PDATA = None
    __FilePth = '/www/server/panel/plugin/qiankeji/json.txt'
    #构造方法
    def  __init__(self):
        pdata = {};
        self.__PDATA = pdata;
        pass

    #自定义访问权限检查
    #一但声明此方法，这意味着可以不登录面板的情况下，直接访问此插件，由_check方法来检测是否有访问权限
    #如果您的插件必需登录后才能访问的话，请不要声明此方法，这可能导致严重的安全漏洞
    #如果权限验证通过，请返回True,否则返回 False 或 public.returnMsg(False,'失败原因')
    #示例未登录面板的情况下访问get_logs方法： /demo/get_logs.json  或 /demo/get_logs.html (使用模板)
    def _check(self, args):
        client_ip = public.GetClientIp()
        public.WriteLog('风控插件请求', str(client_ip)+'发起了风控插件请求')
        if os.path.exists(self.__FilePth):
            file_body = public.ReadFile(self.__FilePth, mode='r')
            jsondata = json.loads(file_body)
            if client_ip != jsondata['ip']:
                return public.returnMsg(False, '请求失败,非法请求!')
            else:
                return True;
        else:
            return public.returnMsg(False, '请求失败,当前未配置IP认证!')

        #token = '123456'
        #limit_addr = ['192.168.1.2','192.168.1.3']
        #if args.token != token: return public.returnMsg(False,'Token验证失败!')
        #if not args.client_ip in limit_addr: return public.returnMsg(False,'IP访问受限!')



    #获取面板日志列表
    #示例已登录面板的情况下访问get_logs方法：/plugin?action=a&name=demo&s=get_logs
    #示例未登录的情况下通过模板输出： /demo/get_logs.html
    #示例未登录的情况下输出JSON： /demo/get_logs.json

    def get_qiankeji(self,args):
        self.__init__();
        #处理前端传过来的参数
        if not 'phone' in args: return public.returnMsg(False, '请输入需要查询的手机号!');
        if os.path.exists(self.__FilePth):
            file_body = public.ReadFile(self.__FilePth, mode='r')
            jsondata = json.loads(file_body)
            self.__PDATA['token'] = jsondata['token'];
            self.__PDATA['phone'] = args.phone;
            result = public.httpPost(self.__APIURL, self.__PDATA)
            return result;
        else:
            return public.returnMsg(False, '请先配置token!');


    def set_config(self, args):
        if not 'ip' in args: return public.returnMsg(False, '请输入IP白名单需要配置的IP!');
        if not 'token' in args: return public.returnMsg(False, '请输入账号绑定的Token!');
        # 如果存在了,则直接修改配置
        if os.path.exists(self.__FilePth):
            f_body = json.dumps({'ip': args.ip, 'token': args.token})
            # 在文件内容里面重新写入新配置的值
            result = public.WriteFile(self.__FilePth, f_body, mode='w+')
            public.WriteLog('修改了配置,操作结果:'+str(result), '配置内容'+f_body)
            return public.returnMsg(result, '');
        else:
            # 第一次初始化配置
            f_body = json.dumps({'ip': args.ip, 'token': args.token})
            # 在文件内容里面写入第一次配置的值,如果文件不存在会自动创建
            result = public.WriteFile(self.__FilePth, f_body, mode='w+')
            public.WriteLog('初始化配置操作结果:'+str(result), '配置内容:'+f_body)
            return public.returnMsg(result, '');

    def get_config(self, args):
        # 如果存在了,则直接返回当前配置
        if os.path.exists(self.__FilePth):
            file_body = public.ReadFile(self.__FilePth, mode='r')
            jsondata = json.loads(file_body)
            return public.returnMsg(True, jsondata);
        else:
            # 第一次初始化配置
            return public.returnMsg(False, '未配置相关配置');







