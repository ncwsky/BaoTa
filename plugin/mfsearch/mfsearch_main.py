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
#|   宝塔第三方应用开发 mfSearch
#+--------------------------------------------------------------------

__all__ = ['mfsearch_main']

import sys,os,json

#设置运行目录
basedir = os.path.abspath(os.path.dirname(__file__))
plugin_path = "/www/server/panel/plugin/mfsearch/"
try:
    os.chdir("/www/server/panel")
except FileNotFoundError:
    os.chdir(os.path.join(basedir, '..', '..'))
    plugin_path = basedir
    

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
    
    
    
class Files:
    @staticmethod
    def search(sTxt, sPath, callback=None, 
               is_re=0, is_word=0, is_case=0, is_deep=0,
               exts=['.xls','.csv','.txt','.log','.html','.sql'], 
               mode=0,
               debug=0):
        """is_re:是否正则匹配,
           sTxt: 需要匹配的文字 如:"13714261894|胡芳芳(\s|$)|4304[0-9]{2}[0-9]{10}[02468]"
           sPath: 需要搜索的路径
           callback: 回调函数
           sTxt: "姓名"只支持UTF-8格式匹配, 
        """
        if not sTxt: return
        #sTxt=sTxt.decode('utf-8').encode('GBK')
        
        import gc,os,re
        #print gc.get_threshold()
        #gc.set_threshold(700, 10, 5)
        if isinstance(exts, str):
            _exts = exts.replace('.','[.]').replace('*','.*').replace(';','|').strip('|')
            _exts = '('+_exts+')'+'$'
        is_re = is_re or mode==2 or is_word or is_case
        if is_re and is_word: 
            if sTxt[0].isalnum():  sTxt=r"\b"+sTxt
            if sTxt[-1].isalnum(): sTxt=sTxt+r"\b"
   
        rs = [] #结果
        
        if not is_deep:
            for f in os.listdir(sPath):
                cs = ''
                fpath = os.path.join(sPath,f)
                if not os.path.isfile(fpath):  continue
                if isinstance(exts, str):
                    if '*.*' not in exts:
                        if not re.match(_exts, f, flags=re.I): continue #match
                else:
                    ext = os.path.splitext(f)[1].lower() 
                    if ext not in exts: continue
                
                try:
                    fp=open(fpath, 'r', encoding='UTF-8')
                except:
                    fp=open(fpath, 'r')
                    
                i = 0
                try:
                    for line in fp: #for line in fp.readlines() #加个readlines很占内存
                        i+=1
                        if is_re :
                            if is_case and not re.search(sTxt, line,flags=re.I): continue
                            elif not is_case and not re.search(sTxt, line): continue
                        else:
                            if line.find(sTxt)==-1: continue 
                        if callback: callback(line, fpath, i)
                        #rs.append([line, fpath])
                except:
                    pass
                fp.close()
        else:
            for root, dirs, files in os.walk(sPath, True, None, False): #遍列目录  #第一次就遍列完目录了,如果再在下层遍列就重复了 
                #处理该文件夹下所有文件: 
                for f in files:
                    cs = ''
                    fpath = os.path.join(root,f)
                    if not os.path.isfile(fpath):  continue
                    if isinstance(exts, str):
                        if '*.*' not in exts:
                            if not re.match(_exts, f, flags=re.I): continue #match
                    else:
                        ext = os.path.splitext(f)[1].lower() 
                        if ext not in exts: continue
                    
                    try:
                        fp=open(fpath, 'r', encoding='UTF-8')
                    except:
                        fp=open(fpath, 'r')
                    i = 0
                    try:
                        for line in fp: #for line in fp.readlines() #加个readlines很占内存
                            i+=1
                            if is_re :
                                if is_case and not re.search(sTxt, line,flags=re.I): continue
                                elif not is_case and not re.search(sTxt, line): continue
                            else:
                                if line.find(sTxt)==-1: continue 
                            if callback: callback(line, fpath, i)
                            #rs.append([line, fpath])
                    except: 
                        pass
                    fp.close()
        return rs 
        
    @staticmethod
    def replace(sTxt, eTxt, sPath, callback=None, 
               is_re=0, is_word=0, is_case=0, is_deep=0,
               exts=['.xls','.csv','.txt','.log','.html','.sql'], 
               mode=0, is_backup=0,
               debug=0):
        
        if not sTxt: return
        
        import zipfile
        import gc,re,time
        if is_backup:
            basedir = os.path.abspath(os.path.dirname(__file__))
            backdir = os.path.join(basedir, 'backups')
            if not os.path.isdir(backdir): os.mkdir(backdir)
            t = time.strftime('%Y%m%d%H%M%S')
            fpath = os.path.join(backdir,  "%s.zip"%t)
            
            try:
                zfile = zipfile.ZipFile(fpath, "w", compression=zipfile.ZIP_DEFLATED)
            except:
                return {}
        
        #print gc.get_threshold()
        #gc.set_threshold(700, 10, 5)
        if isinstance(exts, str):
            _exts = exts.replace('.','[.]').replace('*','.*').replace(';','|').strip('|')
            _exts = '('+_exts+')'+'$'
        is_re = is_re or mode==2 or is_word or is_case
        if is_re and is_word: 
            if sTxt[0].isalnum():  sTxt=r"\b"+sTxt
            if sTxt[-1].isalnum(): sTxt=sTxt+r"\b"
   
        rs = [] #结果
        
        if not is_deep:
            for f in os.listdir(sPath):
                cs = ''
                fpath = os.path.join(sPath,f)
                if not os.path.isfile(fpath):  continue
                if isinstance(exts, str):
                    if '*.*' not in exts:
                        if not re.search(_exts, f, flags=re.I): continue #match
                else:
                    ext = os.path.splitext(f)[1].lower() 
                    if ext not in exts: continue
                
                try:
                    fp=open(fpath, 'r', encoding='UTF-8')
                    encoding = 1
                except:
                    encoding = 0
                    fp=open(fpath, 'r')
                content = fp.read()
                fp.close()
                
                if is_re:
                    if is_case :
                        if not re.search(sTxt, content,flags=re.I): continue
                        content = re.sub(sTxt, eTxt, content, flags=re.I)
                    else:
                        if not re.search(sTxt, content): continue
                        content = re.sub(sTxt, eTxt, content)
                else:
                    if content.find(sTxt)==-1: continue 
                    content = content.replace(sTxt, eTxt)
                if is_backup:
                    bf = fpath.strip('/')
                    zfile.write(fpath, bf) 
                if encoding:
                    with open(fpath, 'w', encoding='UTF-8') as f: f.write(content) 
                else:
                    with open(fpath, 'w') as f: f.write(content)           
                    
                if callback: callback(fpath)
                        
                
        else:
            for root, dirs, files in os.walk(sPath, True, None, False): #遍列目录  #第一次就遍列完目录了,如果再在下层遍列就重复了 
                #处理该文件夹下所有文件: 
                for f in files:
                    cs = ''
                    fpath = os.path.join(root,f)
                    if not os.path.isfile(fpath):  continue
                    if isinstance(exts, str):
                        if '*.*' not in exts:
                            if not re.search(_exts, f, flags=re.I): continue #match
                    else:
                        ext = os.path.splitext(f)[1].lower() 
                        if ext not in exts: continue
                    
                    try:
                        fp=open(fpath, 'r', encoding='UTF-8')
                        encoding = 1
                    except:
                        encoding = 0
                        fp=open(fpath, 'r')
                    content = fp.read()
                    fp.close()
                    
                    if is_re:
                        if is_case :
                            if not re.search(sTxt, content,flags=re.I): continue
                            content = re.sub(sTxt, eTxt, content, flags=re.I)
                        else:
                            if not re.search(sTxt, content): continue
                            content = re.sub(sTxt, eTxt, content)
                    else:
                        if content.find(sTxt)==-1: continue 
                        content = content.replace(sTxt, eTxt)
                    if is_backup:
                        bf = fpath.strip('/')
                        zfile.write(fpath, bf) 
                    if encoding:
                        with open(fpath, 'w', encoding='UTF-8') as f: f.write(content) 
                    else:
                        with open(fpath, 'w') as f: f.write(content)       
                        
                    if callback: callback(fpath)
                    
        if is_backup:
            zfile.close()
        return rs          


class mfsearch_main:
    __plugin_path = plugin_path
    __config = None

    #构造方法
    def  __init__(self):
        pass

    #自定义访问权限检查
    #一但声明此方法，这意味着可以不登录面板的情况下，直接访问此插件，由_check方法来检测是否有访问权限
    #如果您的插件必需登录后才能访问的话，请不要声明此方法，这可能导致严重的安全漏洞
    #如果权限验证通过，请返回True,否则返回 False 或 public.returnMsg(False,'失败原因')
    #示例未登录面板的情况下访问get_logs方法： /mfsearch/get_logs.json  或 /mfsearch/get_logs.html (使用模板)
    def _check_x(self,args):
        #token = '123456'
        #limit_addr = ['192.168.1.2','192.168.1.3']
        #if args.token != token: return public.returnMsg(False,'Token验证失败!')
        #if not args.client_ip in limit_addr: return public.returnMsg(False,'IP访问受限!')
        return True
  
    def get_search(self, args):
        if 'stext' not in args or not args.stext: return {}
        if 'exts' not in args or not args.exts: return {}
        if 'folder' not in args or not args.folder or args.folder=='/': return {}
        mode = int(args.mode) if 'mode' in args else 0
        is_word = int(args.isword) if 'isword' in args else 0
        is_case = int(args.iscase) if 'iscase' in args else 0
        is_deep = int(args.subfold) if 'subfold' in args else 0
        is_re = 1 if  mode==2 else 0
        #sTxt=sTxt.decode('utf-8').encode('GBK')
        
        d = {}
        def callback(line, fpath, i):
            d.setdefault(fpath, {})[str(i)]=line
        Files.search(args.stext, args.folder, callback=callback,
                     exts = args.exts,
                     is_word=is_word, is_case=is_case,mode=mode, is_deep=is_deep
                    )
                            
        _args = {
            'stext':args.stext,'exts':args.exts,'folder':args.folder,'mode':args.mode,
            'isword':is_word,'iscase':is_case, #'stext':args.stext,'stext':args.stext,
            'subfold':is_deep
        } 
        return {'data':d, 'args':_args,'total':len(d)}
        
        
    def get_replace(self, args):
        if 'stext' not in args or not args.stext: return {}
        if 'exts' not in args or not args.exts: return {}
        if 'folder' not in args or not args.folder or args.folder=='/': return {}
        mode = int(args.mode) if 'mode' in args else 0
        is_word = int(args.isword) if 'isword' in args else 0
        is_case = int(args.iscase) if 'iscase' in args else 0
        is_deep = int(args.subfold) if 'subfold' in args else 0
        is_backup = int(args.isbackup) if 'isbackup' in args else 0
        
        is_re = 1 if  mode==2 else 0
        
        d = []
        def callback(fpath):
            d.append(fpath)
            
        Files.replace(args.stext, args.etext, args.folder, callback=callback,
                     exts = args.exts,
                     is_word=is_word, is_case=is_case,mode=mode, is_deep=is_deep,
                     is_backup=is_backup
                    )
                            
        _args = {
            'stext':args.stext,'exts':args.exts,'folder':args.folder,'mode':args.mode,
            'isword':is_word,'iscase':is_case, #'stext':args.stext,'stext':args.stext,
            'subfold':is_deep
        } 
        backupdir = os.path.join(self.__plugin_path, 'backups')
        return {'data':d, 'args':_args, 'total':len(d), 'backupdir':backupdir}    
        

    #获取面板日志列表
    #示例已登录面板的情况下访问get_logs方法：/plugin?action=a&name=mfsearch&s=get_logs
    #示例未登录的情况下通过模板输出： /mfsearch/get_logs.html
    #示例未登录的情况下输出JSON： /mfsearch/get_logs.json

    def get_logs(self,args):
        #处理前端传过来的参数
        if not 'p' in args: args.p = 1
        if not 'rows' in args: args.rows = 12
        if not 'callback' in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)

        #取日志总行数
        count = public.M('logs').count()

        #获取分页数据
        page_data = public.get_page(count,args.p,args.rows,args.callback)

        #获取当前页的数据列表
        log_list = public.M('logs').order('id desc').limit(page_data['shift'] + ',' + page_data['row']).field('id,type,log,addtime').select()
        
        #返回数据到前端
        return {'data': log_list,'page':page_data['page'] }
        
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

