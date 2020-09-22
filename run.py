#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    : 20/7/29 下午2:34
# @Author  : liaozz
# @File    : run.py

"""
    自我介绍一下
"""
from flask import Flask, app, request, Blueprint
import json, traceback, os
from kvm_utils import KVMHelp
import yisu_wu_kvm, os_xml_disk

app = Flask(__name__)


def __get_vnc_token_str():
    path = "/var/noVNC/utils/websockify/token.conf"
    conten = ""
    if os.path.exists(path):
        try:
            with open(path) as token:
                lines = token.readlines()
                conten = "".join(item for item in lines)
        except Exception as e:
            traceback.print_exc()
            pass
    return conten


def __save_vnc_token_str(content):
    path = "/var/noVNC/utils/websockify/token.conf"
    if os.path.exists(path):
        try:
            with open(path, "w") as token:
                token.writelines(content)
        except Exception as e:
            traceback.print_exc()
            pass
    pass


def __may_install_system():
    """
    标准完善的模板镜像
    获取可安装的系统版本
    @return:镜像的文件名*.qocw2  *.iso 列表
    """
    system_version = os_xml_disk.read_mirror_list()
    return system_version


def __del_client_info(data_arg):
    os_version = data_arg.get("os_version")
    result = yisu_wu_kvm.delete_manual_client_mirror(os_version)
    if result:
        print(f"{os_version}没有查到")
        return False
    else:
        return True


def __make_exclusive_mirror(data_arg):
    """
    根据客户自定义模板镜像
    @param data_arg:
    @return:
    """
    s_uuid = data_arg.get("uuid")
    version_num = data_arg.get("version_num")
    print(s_uuid, version_num)
    status = yisu_wu_kvm.make_exclusive_mirror(s_uuid, version_num)
    if status == 1:
        print(f"{s_uuid} xml或者disk不存在")
        return False
    elif status == 2:
        print(f"{s_uuid}自作镜像失败")
        return False
    elif status == 3:
        print(f"{s_uuid}修改{version_num}有重复")
        return False
    else:
        return True


# def __get_exclusive_mirror():
#     """
#     客户定义的模板镜像
#     获取可以模板镜像名
#     @return:列表
#     """
#     mirror_info = os_xml_disk.client_mirror_read_info()
#     mirror_name = (",".join(item for item in mirror_info)).split(",")
#     return mirror_name


def __create_kvm(data_arg):
    """
    param data_dict:
    os_version = *.qcow  ,*.iso
    cpu_num= 1
    memory_num =2000
    disk_size =3
    这里调用创建虚拟机
    :return: data 成功
    status1 服务器名称
    status2 错误会返回1状态
    """
    return_flag = False
    os_version = data_arg.get("os_version")
    cpu_num = data_arg.get("cpu_num")
    memory_num = data_arg.get("memory_num")
    disk_size = data_arg.get("disk_size")
    eth0_ip = data_arg.get("eth0_ip", "dhcp")
    eth0_net = data_arg.get("eth0_net", "255.255.255.0")
    print(os_version, cpu_num, memory_num, disk_size, eth0_ip, eth0_net)
    status1, status2 = yisu_wu_kvm.create_new_os(os_version, cpu_num, memory_num, disk_size, eth0_ip, eth0_net)
    if status2 == 1:
        print(f"创建{status1}机器失败")
        return False
    elif status2 == 2:
        print(f"创建{status1}机器失败")
        return False
    else:
        print(f"创建新机{status1}成功")
        return_flag = status1
        return return_flag


def __delete_kvm(data_arg):
    """
    删除虚拟机
    :return:
    """

    def delete_vnc_token(uuid):
        content = __get_vnc_token_str()
        content_list = content.split("\n")
        co_list = []
        for item in content_list:
            if not uuid in item:
                co_list.append(item)
        __save_vnc_token_str("\n".join(item for item in co_list))

    s_uuid = data_arg.get("uuid")
    status = yisu_wu_kvm.KvmRemoveAdd(s_uuid).remove_server()
    return_flag = False
    if status == 0:
        return_flag = True
        delete_vnc_token(s_uuid)
        print(f"{s_uuid}删除成功")
    elif status == 1:
        print(f"{s_uuid}删除失败")
    else:
        print(f"{s_uuid} 不存在")
    return return_flag


def __add_interface(data_arg):
    '''
    @return:

    '''
    s_uuid = data_arg.get("uuid")
    result = yisu_wu_kvm.KvmRemoveAdd(s_uuid).online_add_interface()
    if result == 0:
        print("添加成功")
        return True
    elif result == 1:
        print("添加失败")
        return False
    else:
        print("已经添加过")
        return True


def __add_new_disk(data_arg):
    '''

    @param data_arg:
    s_uuid = 服务器uuid
    net_disk_size = 1  单位是G
    @return:
    '''
    s_uuid = data_arg.get("s_uuid")
    new_disk_size = data_arg.get("new_disk_size")
    result = yisu_wu_kvm.KvmRemoveAdd(s_uuid).online_add_disk(new_disk_size)
    if result == 0:
        print(f"{s_uuid}添加磁盘成功")
        return True
    else:
        print(f"{s_uuid}添加磁盘失败")
        return False
    pass


def __delete_disk(data_arg):
    '''
    @param data_arg:
    chunk_name = vdb/vdc/vdd
    @return:
    '''
    s_uuid = data_arg.get("s_uuid")
    chunk_name = data_arg.get("chunk_name")
    result = yisu_wu_kvm.KvmRemoveAdd(s_uuid).online_delete_disk(chunk_name)
    if result:
        print(f"{s_uuid}的{chunk_name}删除成功")
        return True
    else:
        print(f"{s_uuid}的{chunk_name}删除失败")
        return False


def __reload_install_os(data_arg):
    eth0_ip = data_arg.get("eth0_ip")
    eth0_netmask = data_arg.get("eth0_netmask")
    s_uuid = data_arg.get("s_uuid")
    os_version = data_arg.get("os_version")
    result = yisu_wu_kvm.reload_install_os(s_uuid, os_version, eth0_ip, eth0_netmask)
    if result:
        print(f"{s_uuid}重装系统成功")
        return True
    else:
        print(f"{s_uuid}重装系统失败")
        return False


def __kvm_info():
    data = None
    try:
        with KVMHelp() as kvm:
            data = kvm.get_kvm_info()
    except Exception as e:
        pass
    # token_str = __get_vnc_token_str()
    token_str = ""
    for item in data:
        token_temp = "%s: 0.0.0.0:%s\n"
        if not item["port"] in token_str:
            token_str = token_str + token_temp % (item["uuid"], item["port"])
    __save_vnc_token_str(token_str)

    return data
    pass


def __power_action(data_dir):
    flag = False
    action = data_dir["js"]
    uuid = data_dir["uuid"]

    with KVMHelp() as kvm:
        flag = kvm.power(uuid, action)
        pass
    return flag


@app.route('/kvm', methods=['POST', 'GET'])
def kvm():
    result = "001"
    desc = "请求失败"
    data = ""
    try:
        if request.method == 'POST':
            data_dir = request.form
            print(data_dir)
            action = data_dir.get("js")
            if action == "create":
                name = __create_kvm(data_dir)
                result = "000"
                desc = "请求成功"
                data = dict(tag=name)
            elif action == "stop" or action == "start" or action == "reboot" or action == "kuaiz":  # 关机
                status = __power_action(data_dir)
                if status:
                    result = "000"
                    desc = "请求成功"
                else:
                    result = "001"
                pass
            elif action == "re_install":
                flag = __reload_install_os(data_dir)
                if flag:
                    result = "000"
                    desc = "请求成功"
            elif action == "kvm_info":
                data = __kvm_info()
                if data:
                    result = "000"
                    desc = "请求成功"
            elif action == "destroy" or action == "delete":
                data = __delete_kvm(data_dir)
                if data:
                    result = "000"
                    desc = "请求成功"
            elif action == "system_qcow" or action == "all_images":
                data = __may_install_system()
                if data:
                    data = (",".join(item for item in data)).split(",")
                    result = "000"
                    desc = "请求成功"
            elif action == "add_eth1":
                flag = __add_interface(data_dir)
                if flag:
                    result = "000"
                    desc = "操作成功"
            elif action == "make_mirror":
                flag = __make_exclusive_mirror(data_dir)
                if flag:
                    result = "000"
                    desc = "操作成功"
            elif action == "del_client":
                flag = __del_client_info(data_dir)
                if flag:
                    result = "000"
                    desc = "操作成功"
                pass
        else:
            # 这里是其他方式请求，不管
            pass
    except Exception as e:
        traceback.print_exc()
        result = "003"
        desc = "请求失败"
        if e.args[0] == "raise":
            data = e.args[1]
        else:
            data = str(e)

    return json.dumps({'result': result, 'desc': desc, 'data': data})


if __name__ == "__main__":
    import sys

    port = sys.argv[1]
    if port:
        app.run(host="0.0.0.0", port=port)
    pass
