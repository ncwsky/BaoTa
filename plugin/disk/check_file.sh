#!/usr/bin/env bash

alias cp=cp
if [ -f /tmp/copy_www.pid ];then
    while [ -f /tmp/copy_www.pid ];do
        sleep 1
        echo "wait"
    done
    #复制完成
    if [ ! -f /www/server/panel/tools.py ];then
        cp -arf /www_backup/server/* /www/server/
    fi

    if [ ! -f /www/server/panel/runserver.py ];then
        cp -arf /www_backup/server/* /www/server/
    fi

    if [ ! -f /www/server/panel/task.py ];then
        cp -arf /www_backup/server/* /www/server/
    fi
    /etc/init.d/bt restart
fi
















