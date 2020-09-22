#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    : 20/9/18 下午5:05
# @Author  : liaozz
# @File    : crontab.py

"""
    定时运行脚本
"""
import os,json,traceback

temp_path="/tmp/temp.txt"
temp_json_path="/tmp/temp.json"

def open_write_json(file_path,data_dict):
    '''
    保存json文件
    :param file_path: 文件路径
    :param data_dict:  字典
    :return:
    '''
    try:
        with open(file_path, "w") as kvm_info:
            json.dump(data_dict, kvm_info, indent=4, ensure_ascii=False)
    except Exception as e:
        traceback.print_exc()
        return False
    return True

def open_read_json(file_path):
    '''
    读取文件
    :param file_path:
    :return:
    '''
    kvm_info_dict=""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as kvm_info:
                kvm_info_dict = json.load(kvm_info)
        except Exception as e:
            traceback.print_exc()
            pass
    return kvm_info_dict
def get_arp_to_temp():
    '''

    :return:
    '''
    os.system('/usr/sbin/arp -a > %s'%temp_path)
    data={}
    with open(temp_path) as fp:
        for line in fp:
            data_array=line.split(" ")
            ip_mac="ip:%s  mac:%s"
            ip=None
            mac=None
            for d in data_array:
                if "(" in d and ")" in d:
                    ip=d.replace("(","").replace(")","")
                if ":" in d:
                    mac=d

            if ip and mac :
                data[mac]=ip
    open_write_json(temp_json_path,data)
def get_ip_from_mac(mac):
    ips=[]
    macs=str(mac).split(",")
    data_dict=open_read_json(temp_json_path)
    for m  in macs:
        if data_dict and data_dict.get(m):
            ip=data_dict[m]
            ips.append(ip)
    return ",".join(ips)


    pass
if __name__ == "__main__":
    get_arp_to_temp()
    pass
