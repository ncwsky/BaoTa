#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 邹浩文 <627622230@qq.com>
# +-------------------------------------------------------------------

#--------------------------------
# Dns管理器
#--------------------------------

import os
os.chdir("/www/server/panel")
import public, re, psutil, json
try:
    import urllib2
except:
    import urllib as urllib2
class dns_manager_main(object):
    def __init__(self):
        self.net_path = "/etc/sysconfig/network-scripts/"
        self.config = "/www/server/panel/plugin/dns_manager/config.json"
        self.path = "/www/server/panel/plugin/dns_manager/"
        self.dns_conf_path = "/var/named/chroot"
        self.zone_file = self.dns_conf_path + "/etc/named.rfc1912.zones"

    # # 获取公网ip
    def __check_pubilc_ip(self):
        try:
            url = 'http://pv.sohu.com/cityjson?ie=utf-8'
            opener = urllib2.urlopen(url)
            m_str = opener.read()
            ip_address = re.search('\d+.\d+.\d+.\d+', m_str).group(0)
            c_ip = public.check_ip(ip_address)
            if not c_ip:
                a, e = public.ExecShell("curl ifconfig.me")
                return a
            return ip_address
        except:
            filename = '/www/server/panel/data/iplist.txt'
            ip_address = public.readFile(filename).strip()
            if ip_address:
                return ip_address
            else:
                return False
    # 获取公网网卡
    def __check_card(self,ip):
        net_info = psutil.net_if_addrs()
        if net_info:
            for card in net_info.values():
                if ip == card[0].address:
                    return {"ip": True}

    # 构造子网卡名和获取网卡
    def __get_sub_card_name(self):
        net_card = {}
        net_info = psutil.net_if_addrs()
        for card in net_info.keys():
            card_name_list = ["eth","ens","em"]
            for i in card_name_list:
                if i in card:
                    sub_card = "{}:0".format(card)
                    net_card["sub_card"] = sub_card
                    net_card["card"] = card
                    return net_card

    # 备份网卡配置
    def __back_card(self):
        net_card = self.__get_sub_card_name()
        source = self.net_path + "ifcfg-" + net_card["card"]
        target = source + "_bak"
        os.system("cp {0} {1}".format(source, target))

    # 还原所有网卡配置
    def __restore_card(self):
        net_card = self.__get_sub_card_name()
        sub_card = self.net_path + "ifcfg-" + net_card["sub_card"]
        source = self.net_path + "ifcfg-" + net_card["card"]
        target = source + "_bak"
        os.system("rm -f {0} && ifdown {1}".format(sub_card, net_card["sub_card"]))
        os.system("rm -f {0} && mv {1} {0}".format(source, target))
        os.system("ifdown {0} && ifup {0}".format(net_card["card"]))

    # 创建子网卡
    def __create_subcard(self,ip):
        self.__back_card()
        net_card = self.__get_sub_card_name()
        sub_card = net_card["sub_card"]
        if sub_card:
            content = """DEVICE={0}
IPADDR={1}
NETMASK=255.255.255.0
ONBOOT=yes
"""
            content = content.format(sub_card, ip)
            sub_card_path = self.net_path + "ifcfg-" + sub_card
            public.writeFile(sub_card_path, content)
            public.ExecShell("ifup {}".format(sub_card))
        if not self.__check_net_work():
            self.__restore_card()
            return public.ReturnMsg(False, "配置失败，无法使用公网访问请联系官方人员")
        return public.ReturnMsg(True, "配置成功")

    # 获取可以监听的IP
    def get_can_listen_ip(self,get):
        public_ip = self.__check_pubilc_ip()
        net_info = psutil.net_if_addrs()
        addr = []
        for i in net_info.values():
            if i[0].address == "127.0.0.1":
                continue
            addr.append(i[0].address)
        if not public_ip in addr:
            addr.append(public_ip)
        addr.append('any')
        return addr

    # 选择监听地址
    def set_listen_ip(self,get):
        values = self.__check_give_vaule(get)
        ip = values["listen_ip"]
        if not self.__check_card(ip):
            result = self.__create_subcard(ip)
            if not result["status"]:
                return result
        conffile = self.dns_conf_path+"/etc/named.conf"
        self.__back_file(conffile)
        conf = public.readFile(conffile)
        rep = "\d+\s+\{\s*([\w\.]+)"
        if ":" in ip:
            rep = "\d+\s+\{\s*([\w\:]+)"
        new_conf = re.sub(rep,"53 { "+values["listen_ip"],conf)
        public.writeFile(conffile,new_conf)
        cc = self.__check_conf()
        if cc:
            self.__restore_file(conffile)
            return public.ReturnMsg(False, "配置失败 "+ str(cc))
        config = self.__read_config(self.config)
        config["listen_ip"] = ip
        self.__write_config(self.config,config)
        os.system("systemctl restart named-chroot")
        return public.ReturnMsg(True, "配置成功")

    # 获取监听ip
    def __get_listen_ip(self):
        config = self.__read_config(self.config)
        return config["listen_ip"]

    # 检测网络连接
    def __check_net_work(self):
        urlList = ["http://www.baidu.com", "http://www.google.com"]
        for url in urlList:
            try:
                opener = urllib2.urlopen(url)
                opener.read()
                return True
            except:
                return False

    # 创建默认域名解析配置
    def __create_dns_resolve(self, domain):
        ip = self.__get_listen_ip()
        if str(ip) == "any":
            ip = self.__check_pubilc_ip()
        type = "A"
        if ":" in ip:
            type = "AAAA"
        resolve_file = "{0}/var/named/{1}.zone".format(self.dns_conf_path, domain)
        resolve_conf = """$TTL 1D
{0}.      IN SOA  f1g1ns1.dnspod.net.     admin.{0}. (
                                        0       ; serial
                                        1D      ; refresh
                                        1H      ; retry
                                        1W      ; expire
                                        3H )    ; minimum
{0}.            86400   IN      NS         ns1.{0}.
{0}.            86400   IN      NS         ns2.{0}.
{0}.            600     IN      {2}            {1}
{0}.            600     IN      MX 10        mail.{0}.
www             600     IN      {2}        {1}
mail            600     IN      {2}        {1}
ns1             600     IN      {2}        {1}
ns2             600     IN      {2}        {1}
""".format(domain, ip, type)
        public.writeFile(resolve_file, resolve_conf)
        self.__back_file(resolve_file, act="def")
        return True

    # 测试域名解析
    def __check_domain_resolve(self, domain, host="",type="A"):
        import dns.resolver
        ip = self.__get_listen_ip()
        if str(ip) == "any":
            ip = self.__check_pubilc_ip()
        my_resolver = dns.resolver.Resolver()
        my_resolver.nameservers = [ip]
        if host:
            domain = host+"."+domain
        try:
            a = my_resolver.query(domain, type)
            for i in a.response.answer:
                for j in i.items:
                    return j
        except:
            pass

    # 检查域名是否已经存在
    def __check_domain_exist(self,domain):
        config = self.__read_config(self.config)
        for i in config["domain"]:
            if i in domain or domain in i:
                return True

    # 读配置
    def __read_config(self, path):
        if not os.path.exists(path) or not public.readFile(path):
                public.writeFile(path, json.dumps({"domain":[],"listen_ip":""}))
        upBody = public.readFile(path)
        return json.loads(upBody)

    # 写配置
    def __write_config(self ,path, data):
        return public.writeFile(path, json.dumps(data))

    # 添加二级域
    def add_domain(self, get):
        self.__release_port(get)
        values = self.__check_give_vaule(get)
        if "status" in values.keys():
            return values
        domain = values["domain"]
        if self.__check_domain_exist(domain):
            return public.ReturnMsg(False, "域名已经存在")
        zone_config = """
zone "%s" IN {
        type master;
        file "%s.zone";
        allow-update { none; };
};
""" % (domain, domain)
        self.__back_file(self.zone_file)
        public.writeFile(self.zone_file,zone_config,"a+")
        if self.__create_dns_resolve(domain):
            cc = self.__check_conf()
            if cc:
                self.__restore_file(self.zone_file)
                resolve_file = "{0}/var/named/{1}.zone".format(self.dns_conf_path, domain)
                os.remove(resolve_file)
                return public.ReturnMsg(False, "添加域名失败 " + str(cc))
            os.system("systemctl restart named-chroot")
            if self.__check_domain_resolve(domain):
                config = self.__read_config(self.config)
                config["domain"].append(domain)
                self.__write_config(self.config, config)
                public.WriteLog('DNS服务', '添加域名[' + domain + ']成功')
                return public.ReturnMsg(True, "添加域名成功")
        public.WriteLog('DNS服务', '添加域名[' + domain + ']失败')
        self.__restore_file(self.zone_file)
        return public.ReturnMsg(False, "添加域名失败")

    # 获取域名列表
    def get_domain_list(self, get):
        config = self.__read_config(self.config)
        if config["domain"]:
            return public.ReturnMsg(True, config["domain"])
        if not self.__get_listen_ip():
            return "0"
        return public.ReturnMsg(True, config["domain"])

    # 删除区域配置
    def __delete_zone(self,domain):
        zone_conf = public.readFile(self.zone_file)
        rep = '\nzone\s+"%s"(.|\n)+"%s.+\n\s+allow.+\n};\n' % (domain,domain)
        zone_conf = re.sub(rep,"",zone_conf)
        public.writeFile(self.zone_file,zone_conf)

    # 删除域名
    def delete_domain(self, get):
        values = self.__check_give_vaule(get)
        if "status" in values.keys():
            return values
        domain = values["domain"]
        config = self.__read_config(self.config)
        if domain in config["domain"]:
            config["domain"].remove(domain)
            self.__write_config(self.config,config)
            resolve_file = "{0}/var/named/{1}.zone".format(self.dns_conf_path, domain)
            os.remove(resolve_file)
            self.__delete_zone(domain)
            os.system("systemctl restart named-chroot")
            public.WriteLog('DNS服务', '删除域名[' + domain + ']成功')
            return public.ReturnMsg(True, "删除成功")

    # 判断解析是否存在
    def __check_resolve_exist(self,zone_file,values):
        v = values.copy()
        if "id" in v:
            id = v["id"]
        else:
            id = ""
        if v["act"] == "modify" and id:
            old_conf = self.__read_config(self.path+"tmp")
            old_conf = old_conf[str(id)]
            if "MX" in old_conf:
                v["host"] = old_conf[0]
                v["ttl"] = old_conf[1]
                v["type"] = old_conf[2]
                v["mx_priority"] = old_conf[3]
                v["value"] = old_conf[4]
            else:
                v["host"] = old_conf[0]
                v["ttl"] = old_conf[1]
                v["type"] = old_conf[2]
                v["value"] = old_conf[3]
        if v["act"] != "add":
            v["value"] = ".+"
        with open(zone_file) as f:
            for i in f.readlines():
                if v["host"] == i.split()[0] and v["act"] == "add":
                    return True
                rep = "{host}\s+{ttl}\s+IN\s+{type}\s+{value}".format(host=v["host"], type=v["type"], ttl=v["ttl"],
                                                                       value=v["value"])
                if v["type"] == "MX":
                    rep = "{host}\s+{ttl}\s+IN\s+{type}\s+{mx_priority}\s+{value}".format(host=v["host"], type=v["type"],
                                                                                          mx_priority=v["mx_priority"],
                                                                                          ttl=v["ttl"], value=v["value"])
                result = re.search(rep, i)
                if result:
                    return result

    # 备份配置文件
    def __back_file(self, file, act=None):
        file_type = "_bak"
        if act:
            file_type = "_def"
        os.system("/usr/bin/cp -p {0} {1}".format(file, file + file_type))

    # 还原配置文件
    def __restore_file(self, file, act=None):
        file_type = "_bak"
        if act:
            file_type = "_def"
        os.system("/usr/bin/cp -p {1} {0}".format(file, file + file_type))

    # 测试配置文件
    def __check_conf(self):
        a, e = public.ExecShell("/usr/sbin/named-checkconf -t /var/named/chroot -z")
        c = re.search("(error|failed|missing)", a)
        if c or e:
            return [a,e]

    # 解析域名文件
    def __edit_resolve_file(self, zone_file, act, values):
        add_resolve = "{host}\t{ttl}\tIN\t{type}\t{value}\n".format(host=values["host"], type=values["type"], ttl=values["ttl"],value=values["value"])
        if values["type"] == "MX":
            add_resolve = "{host}\t{ttl}\tIN\t{type}\t{mx_priority}\t{value}\n".format(host=values["host"], type=values["type"],mx_priority=values["mx_priority"],ttl=values["ttl"], value=values["value"])
        result = self.__check_resolve_exist(zone_file, values)
        zone_conf = public.readFile(zone_file)
        if act == "add" and result:
            return True
        self.__back_file(zone_file)
        if act == "add" and not result:
            public.writeFile(zone_file, add_resolve, "a+")
        if act == "delete" and result:
            tmp = zone_conf.replace(result.group(0),"")
            new_conf = ""
            for i in tmp.splitlines():
                if i:
                    new_conf += i+"\n"
            public.writeFile(zone_file, new_conf)
        if act == "modify" and result:
            tmp = zone_conf.replace(result.group(0), add_resolve[:-1])
            public.writeFile(zone_file, tmp)
        if self.__check_conf():
            self.__restore_file(zone_file)
            return True

    # 操作解析
    def act_resolve(self, get):
        values = self.__check_give_vaule(get)
        if "status" in values.keys():
            return values
        domain = values["domain"]
        act = values["act"]
        d = {"delete":"刪除","add":"添加","modify":"修改"}
        zone_dir = "/var/named/chroot/var/named/"
        zone_files = os.listdir(zone_dir)
        get_file = domain + ".zone"
        for i in zone_files:
            if get_file == i:
                zone_file = zone_dir+get_file
                if not self.__edit_resolve_file(zone_file, act, values):
                    os.system("systemctl restart named-chroot")
                    v = values["host"]
                    if v == "@":
                        v = ""
                    if values["type"] != "NS":
                        if not self.__check_domain_resolve(domain, host=v,type=values["type"]) and values["act"] == "delete":
                            public.WriteLog('DNS服务', '{0} 解析 {1}成功'.format(domain, d[act]))
                            return public.ReturnMsg(True, '{0}成功'.format(d[act]))
                        elif self.__check_domain_resolve(domain, host=v,type=values["type"]) and values["act"] != "delete":
                                public.WriteLog('DNS服务', '{0} 解析 {1}成功'.format(domain, d[act]))
                                return public.ReturnMsg(True, '{0}成功'.format(d[act]))
                    else:
                        public.WriteLog('DNS服务', '{0} 解析 {1}成功'.format(domain, d[act]))
                        return public.ReturnMsg(True, '{0}成功'.format(d[act]))
                public.WriteLog('DNS服务', '解析 {0}失败, 请检查主机名是否已经存在'.format(domain,d[act]))
                return public.ReturnMsg(False, '{0}失败，请检查主机名是否已经存在'.format(d[act]))

    # 配置转换json
    def __change_json(self, data):
        conf_json = {}
        n = 0
        for i in data.splitlines():
            rep = "([\w\.]+|@)\s+(\d+)\s+\w+\s+(\w+)\s+([\w\.]+.*)"
            if "MX" in i:
                rep = "([\w\.]+|@)\s+(\d+)\s+\w+\s+(\w+)\s+(\w+)\s+([\w\.]+.*)"
            result = re.search(rep, i)
            if result:
                # result_list = result.group().split()
                # result_list.remove("IN")
                if "MX" in i:
                    result_list = [result.group(1), result.group(2), result.group(3), result.group(4), result.group(5)]
                else:
                    result_list = [result.group(1),result.group(2),result.group(3),result.group(4)]
                conf_json[str(n)] = result_list
                n += 1
        public.writeFile(self.path+"tmp",json.dumps(conf_json))
        return conf_json

    # 取域名解析
    def get_resolve(self,get):
        values = self.__check_give_vaule(get)
        if "status" in values.keys():
            return values
        domain = values["domain"]
        zone_dir = "/var/named/chroot/var/named/"
        zone_files = os.listdir(zone_dir)
        get_file = domain + ".zone"
        for i in zone_files:
            if get_file == i:
                zone_file = zone_dir+get_file
                zone_conf = public.readFile(zone_file)
                return self.__change_json(zone_conf)

    # 恢复默认配置解析
    def restore_def_resolve(self, get):
        values = self.__check_give_vaule(get)
        domain = values["domain"]
        resolve_file = "{0}/var/named/{1}.zone".format(self.dns_conf_path, domain)
        self.__restore_file(resolve_file, act="def")
        public.WriteLog('DNS服务', '恢复默认解析成功')
        os.system("systemctl restart named-chroot")
        return public.ReturnMsg(True, "恢复成功")

    # 获取日志
    def get_logs(self, get):
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', (u'DNS服务',)).count()
        limit = 10
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}

        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs').where('type=?', (u'DNS服务',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    def clearup_logs(self,get):
        public.M('logs').where('type=?', (u'DNS服务',)).delete()
        return public.ReturnMsg(True, "清理成功")

    # 获取服务状态
    def get_service_status(self,get):
        sh = "ps aux|grep named|grep -v 'grep'"
        a,e = public.ExecShell(sh)
        if (a):
            return True
        else:
            return False

    # 停止服务
    def stop_service(self,get):
        import time
        os.system("systemctl stop named-chroot")
        time.sleep(1)
        if self.get_service_status(get):
            os.system("pkill -9 named")
        if self.get_service_status(get):
            return public.ReturnMsg(False, "停止服务失败")
        return public.ReturnMsg(True, "停止服务成功")

    # 启动服务
    def start_service(self,get):
        if not self.get_service_status(get):
            os.system("systemctl start named-chroot")
            if not self.get_service_status(get):
                return public.ReturnMsg(False, "启动服务失败")
            return public.ReturnMsg(True, "启动服务成功")
        return public.ReturnMsg(False, "服务已经启动，无需启动")

    def __first_check(self):
        if public.readFile(self.path+"first.txt"):
            return True
        public.writeFile(self.path+"first.txt","1")

    #放行dns端口
    def __release_port(self,get):
        try:
            import firewalls
            port = ["53", "953"]
            for p in port:
                access_port = public.M('firewall').where("port=?", (p,)).count()
                if int(access_port) > 0:
                    continue
                get.port = p
                get.ps = 'DNS'
                firewalls.firewalls().AddAcceptPort(get)
            return port
        except:
            return False

    # 检查输入参数
    def __check_give_vaule(self, get):
        values = {}
        rep_ip = "^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$"
        rep_ipv6 = "^\s*((([0-9A-Fa-f]{1,4}:){7}(([0-9A-Fa-f]{1,4})|:))|(([0-9A-Fa-f]{1,4}:){6}(:|((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})|(:[0-9A-Fa-f]{1,4})))|(([0-9A-Fa-f]{1,4}:){5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){4}(:[0-9A-Fa-f]{1,4}){0,1}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){3}(:[0-9A-Fa-f]{1,4}){0,2}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){2}(:[0-9A-Fa-f]{1,4}){0,3}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:)(:[0-9A-Fa-f]{1,4}){0,4}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(:(:[0-9A-Fa-f]{1,4}){0,5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})))(%.+)?\s*$"
        rep_host = "^[a-zA-Z0-9\_]+\-{0,1}\_{0,1}[a-zA-Z0-9\_]*$"
        rep_domain_point = "^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.$"
        rep_domain = "^(?=^.{3,255}$)[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+$"
        if hasattr(get, "id"):
            values["id"] = int(get.id)
        if hasattr(get, "domain"):
            if re.search(rep_domain, get.domain):
                values["domain"] = str(get.domain)
            else:
                return public.ReturnMsg(False, "请检查域名格式是否正确")
        if hasattr(get, "host"):
            if re.search(rep_domain, get.host):
                values["host"] = str(get.host)
            elif re.search(rep_host, get.host):
                values["host"] = str(get.host)
            elif re.search(rep_domain_point, get.host):
                values["host"] = str(get.host)
            elif get.host == "@":
                values["host"] = str(get.host)
            else:
                return public.ReturnMsg(False, "请检主机名格式是否正确")
        if hasattr(get, "type"):
            rep = "(NS|A|CNAME|MX|TXT|AAAA|SRV)"
            if re.search(rep, get.type):
                values["type"] = str(get.type)
            else:
                return public.ReturnMsg(False, "请检解析类型格式是否正确")
        if hasattr(get, "ttl"):
            try:
                values["ttl"] = int(get.ttl)
            except:
                return public.ReturnMsg(False, "请检TTL值格式是否正确")
        if hasattr(get, "mx_priority"):
            try:
                values["mx_priority"] = int(get.mx_priority)
            except:
                return public.ReturnMsg(False, "请检MX优先级格式是否正确")
        if hasattr(get, "act"):
            l = ["delete", "add", "modify"]
            if get.act in l:
                values["act"] = get.act
            else:
                return public.ReturnMsg(False, "请检操作类型格式是否正确")
        if hasattr(get,"listen_ip"):
            if re.search(rep_ip,get.listen_ip) or re.search(rep_ipv6,get.listen_ip) or get.listen_ip == "any":
                values["listen_ip"] = get.listen_ip
            else:
                return public.ReturnMsg(False, "请检IP地址格式是否正确")
        if hasattr(get, "value"):
            try:
                if values["type"] == "A":
                    if re.search(rep_ip, get.value):
                        values["value"] = str(get.value)
                if values["type"] == "NS":
                    if re.search(rep_ip, get.value):
                        values["value"] = str(get.value)+"."
                    if re.search(rep_domain, get.value):
                        values["value"] = str(get.value) + "."
                    if re.search(rep_domain_point, get.value):
                        values["value"] = str(get.value)
                    if re.search(rep_host, get.value):
                        values["value"] = str(get.value) + "."
                if values["type"] == "CNAME":
                    if re.search(rep_domain_point, get.value):
                        values["value"] = str(get.value)
                    if re.search(rep_domain, get.value):
                        values["value"] = str(get.value) + "."
                if values["type"] == "MX":
                    if re.search(rep_domain_point, get.value):
                        values["value"] = str(get.value)
                    if re.search(rep_domain, get.value):
                        values["value"] = str(get.value) + "."
                    if re.search(rep_ip, get.value):
                        values["value"] = str(get.value)+ "."
                if values["type"] == "TXT":
                    values["value"] = str(get.value)
                if values["type"] == "AAAA":
                    if re.search(rep_ipv6, get.value):
                        values["value"] = str(get.value)
                if values["type"] == "SRV":
                    values["value"] = str(get.value)
                if "value" not in values: return public.ReturnMsg(False, "请检查记录值格式是否正确")
            except Exception as e:
                return public.ReturnMsg(False, "请检查记录值格式是否正确")
        return values


# class get:
#     pass
# get.domain = "youbadbad.cn"
# # get.host = "www"
# # get.type = "A"
# # get.ttl = "600"
# get.listen_ip = "192.168.1.198"
#
# d = dns_manager_main()
# print(d.get_listen_ip())