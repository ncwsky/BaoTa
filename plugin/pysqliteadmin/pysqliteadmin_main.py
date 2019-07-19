#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# editor: mufei(ypdh@qq.com tel:15712150708)
'''
牧飞 _ __ ___   ___   ___  / _| ___(_)
| '_ ` _ \ / _ \ / _ \| |_ / _ \ |
| | | | | | (_) | (_) |  _|  __/ |
|_| |_| |_|\___/ \___/|_|  \___|_|
'''
#+--------------------------------------------------------------------
#|   宝塔第三方应用开发 pysqliteadmin
#+--------------------------------------------------------------------
import sys,os,json

#设置运行目录
basedir = os.path.abspath(os.path.dirname(__file__))
plugin_path = "/www/server/panel/plugin/pysqliteadmin/"
try:
    os.chdir("/www/server/panel")
except FileNotFoundError:
    print("FileNotFoundError") 
    os.chdir(os.path.join(basedir, '..', '..'))
    plugin_path = basedir.rstrip('/')+'/'

#添加包引用位置并引用公共包
sys.path.append("class/")
import public

__all__ = ["pysqliteadmin_main"]

from BTPanel import app, cache,session
from flask import render_template, request,redirect, url_for

prefix="pysqliteadmin"

from views import *
from pysqliteadmin_config import initialize_db
import peewee

   


class pysqliteadmin_main:
    "sqlite3数据库web可视化操作"
    
    __plugin_path = plugin_path
    __config = None
    
    #构造方法
    def  __init__(self):
        pass
        

    def set_db(self, args):
        err = {'error':'sqlite3文件不能为空或不存在!'}
        if not 'db_file' in args: return err
        db_file = args.db_file
        if not os.path.isfile(db_file): return err
        try:
            initialize_db(db_file)
        except peewee.DatabaseError:
            return {'error':'file is not a database!'}
           
        return {'result':True}
    
    def get_scan(self, args):
        if not ('folder' in args and args.folder): return {'error':'搜索目录不能为空'}
        if not os.path.isdir(args.folder): return {'error':'搜索目录不存在'}
        exts = args.exts if 'exts' in args else '*.db;*.sqlite;*sqlite3'
        rs = scan_sqlite3(args.folder, exts=exts, callback=None)
        rs = [s.replace('\\','/') for s in rs]
        return {'result':rs}
    
    
        
        
    