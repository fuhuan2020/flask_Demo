#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re, subprocess, os, json, uuid
from random import randint
import xml
import logging
from kvm_utils import KVMHelp
import os_xml_disk
import traceback
import libvirt

disk_path = "/data/kvm/"  # 虚拟机磁盘存放目录_判断
file_path = "/etc/libvirt/qemu/"  # 虚拟机文件目录_判断
os_args_file = "/data/template/test.txt"  # 虚拟机信息保存路径
template_dir = "/data/template"
client_template_dir = "/data/client/template"
client_template_mirror_storage_info = "/data/client/mirror.json"
os_install_info_file = "/data/template/os_info.json"
template_os_file = "/data/template/xml/template-os.xml"
tmp_interface = "/data/tmp_inter"
original_iso = "/data/iso"

LOG_FORMAT = "[%(asctime)s]  [%(levelname)s] [%(name)s] [%(pathname)s] --> %(message)s "
# LOG_FORMAT = "%(asctime)s  %(levelname)s %(pathname)s %(message)s "
DATE_FORMAT = '%Y-%m-%d  %H:%M:%S %a '
logging.basicConfig(level=logging.DEBUG,
                    format=LOG_FORMAT,
                    datefmt=DATE_FORMAT,
                    filename=r"/var/log/kvm.log",
                    filemode='a',
                    )


class KvmRemoveAdd(object):
    def __init__(self, s_uuid):
        self.s_uuid = s_uuid
        self.s_name = None

    # 获取服务器信息
    def get_os_info(self):
        with open(os_args_file, "r") as f_read:
            lines = f_read.readlines()
            for line in lines:
                if self.s_uuid in line:
                    self.s_name = line.split(",")[1]
        if self.s_name:
            system_info = {}
            bridge_num = []
            disk_num_info = {}
            DOMTree = xml.dom.minidom.parse(f"/etc/libvirt/qemu/{self.s_name}.xml")
            collection = DOMTree.documentElement
            if collection.hasAttribute("type"):
                print("Root element : %s" % collection.getAttribute("type"))
            interfaces = collection.getElementsByTagName("interface")
            for i in interfaces:
                bridge_num.append(i.childNodes[3].getAttribute("bridge"))
            disk_name = "no name"
            disk_path_file = "no disk"
            for name in collection.getElementsByTagName("disk"):
                for a in name.getElementsByTagName("target"):
                    if not a.getAttribute("dev") == "hda":
                        disk_name = a.getAttribute("dev")
                for b in name.getElementsByTagName("source"):
                    disk_path_file = b.getAttribute("file")
                disk_num_info[disk_name] = disk_path_file
            vnc_port = collection.getElementsByTagName("graphics")[0].getAttribute("port")

            system_info["s_bridge"] = bridge_num
            system_info["s_disks"] = disk_num_info
            system_info["s_name"] = self.s_name
            system_info['s_uuid'] = self.s_uuid
            system_info["s_port"] = vnc_port
            return system_info
        else:
            raise Exception("提供的uuid不存在查不到机器")

    def remove_stored_info(self):
        with open(os_args_file, "r") as f_read:
            lines = f_read.readlines()
        with open(os_args_file, "w") as f_w:
            for line in lines:
                if self.s_uuid in line:
                    continue
                f_w.write(line)

    def remove_server(self):
        """
        查询改机信息，如是开机强制关机再删除
        @return: 0:删除成功 1:删除失败
        """
        logger = logging.getLogger("remove_server")
        try:
            with KVMHelp() as kvm_info:
                servers_info = kvm_info.get_kvm_info()
                for server_info in servers_info:
                    if self.s_uuid in server_info["uuid"]:
                        if int(server_info["status"]):  # 强制关机
                            kvm_info.power(self.s_uuid, "destroy")
                        # undefine 删除磁盘  清除记录
                        system_info = self.get_os_info()
                        disk_info = system_info["s_disks"]
                        result = kvm_info.power(self.s_uuid, "undefine")
                        if result == 0:
                            self.remove_stored_info()
                            for disk_file in disk_info.values():
                                subprocess.call(f"rm -f {disk_file}", shell=True)
                            logger.debug(f"{server_info['name']}(uuid:{server_info['uuid']})删除成功")
                            return 0
        except Exception as e:
            print(e)
            logger.error(f"*{server_info['name']}(uuid:{server_info['uuid']})undefine删除失败*:{traceback.format_exc()}")
            return 1

    def online_add_interface(self):
        """
        @return:
        0 成功
        1 添加失败
        2 已经存在该网卡
        """
        logger = logging.getLogger("add_interface")
        system_info = self.get_os_info()
        s_name = system_info["s_name"]
        list_bridge = system_info["s_bridge"]
        if "br1" in list_bridge:
            logger.debug(f"{s_name}({self.s_uuid})网卡已经在br1上")
            return 2
        else:
            result = subprocess.call(
                f"virsh attach-interface  {s_name} --type bridge --source br1 --model virtio --persistent",
                shell=True)
            if result == 0:
                logger.debug(f"{s_name}({self.s_uuid})网卡已经在br1上添加成功")
                return 0
            else:
                logger.error(f"{s_name}({self.s_uuid})网卡已经在br1上失败")
                return 1

    def online_add_disk(self, new_disk_size):
        """
        @param new_disk_size: 添加磁盘大小
        @return:
        0 ok
        1 添加磁盘报错
        2 创建新磁盘报错
        """
        logger = logging.getLogger("add_disk")
        system_info = self.get_os_info()
        disk_info = system_info["s_disks"]
        server_name = system_info["s_name"]
        disk_num = ["vda", "vdb", "vdc", "vdd", 'vde', 'vdf', 'vdg', 'vdh']
        for chunk_name in disk_num:
            if chunk_name in disk_info.keys():
                continue
            else:
                new_disk_name = f"{disk_path}{server_name}_{chunk_name}_{new_disk_size}.qcow2 "
                try:
                    subprocess.check_call(
                        f"qemu-img   create  -f  qcow2 {new_disk_name}   {new_disk_size}G",
                        shell=True)
                    subprocess.check_call(
                        f"virsh attach-disk {server_name} {new_disk_name} {chunk_name} --cache=none --subdriver=qcow2 --persistent",
                        shell=True)

                    logger.debug(f"创建{server_name}的{chunk_name}磁盘{new_disk_size}G并添加成功")
                    return 0
                except Exception as e:
                    subprocess.call(f"rm -rf {new_disk_name}")
                    print(e)
                    logger.error(f"{server_name}的{chunk_name}磁盘{new_disk_size}G添加失败:{traceback.format_exc()}")
                    return 1

    def online_delete_disk(self, chunk_name):
        """
        @param chunk_name: 磁盘块名 vdb vdc
        @return:
        """
        logger = logging.getLogger("delete_disk")
        system_info = self.get_os_info()
        disk_info = system_info["s_disks"]
        server_name = system_info["s_name"]
        if chunk_name in disk_info.keys() and chunk_name != "vda":
            subprocess.call(f"virsh detach-disk {server_name}  {chunk_name} --persistent ", shell=True)
            logger.debug(f"{server_name}的{chunk_name}盘删除成功")
            return True
        else:
            logger.error(f"{server_name}的{chunk_name}盘删除失败")
            return False


def create_xml_info():
    """
    xml配置文件需要的vnc端口，mac,名字，uuid
    @param: os_version：虚拟机名
    @return:
    """
    with open(os_args_file, "a+") as f_read:
        con = str(f_read.readlines())
        while True:
            s_port = str(randint(9000, 9999))
            # s_mac = ":".join(["%02x" % x for x in map(lambda x: randint(0, 254), range(6))])
            mac_list = [0x60, 0x16, 0x3e, randint(0x00, 0x7f), randint(0x00, 0xff), randint(0x00, 0xff)]
            s_mac = ':'.join(map(lambda x: "%02x" % x, mac_list))
            if re.findall(s_port, con) or re.findall(s_mac, con):
                pass
            else:
                # s_name = os_version + "-test-" + s_port
                s_uuid = uuid.uuid1()
                return s_uuid, s_mac, s_port


def global_args_if():
    # 选取判断global参数是否存在
    dir_files = [disk_path, file_path, template_dir]
    for i in dir_files:
        if not os.path.exists(i):
            print(f"{i}文件或者目录不存在")
            return False
    return True


def interface_eth0_file(ip_1, netmask_1, vnc_port):
    # ip = "192.168.10.3"
    # netmask = "255.255.255.0"
    if "dhcp" in ip_1:
        int_eth0 = f'''NAME=eth0
DEVICE=eth0
ONBOOT=yes
NETBOOT=yes
NM_CONTROLLED=no
IPV6INIT=yes
BOOTPROTO=dhcp
TYPE=Ethernet
'''
    else:
        int_eth0 = f'''NAME=eth0
DEVICE=eth0
ONBOOT=yes
NETBOOT=yes
NM_CONTROLLED=no
IPV6INIT=yes
BOOTPROTO=static
TYPE=Ethernet
IPADDR={ip_1}
NETMASK={netmask_1}'''
    tmp_interface_dir = f"{tmp_interface}/{vnc_port}"
    if not os.path.exists(tmp_interface_dir):
        os.makedirs(tmp_interface_dir)
    with open(f'{tmp_interface_dir}/ifcfg-eth0', 'w') as f_w:
        f_w.write(int_eth0)
        return tmp_interface_dir


def u_interface_eth0_file(ip_1, netmask_1, vnc_port):
    if "dhcp" in ip_1:
        int_eth0 = f'''auto lo
iface lo inet loopback
auto eth0
iface eth0 inet dhcp
'''
    else:
        int_eth0 = f'''auto lo
iface lo inet loopback
auto eth0
iface eth0 inet static
address {ip_1}
netmask {netmask_1}
'''
    tmp_interface_dir = f"{tmp_interface}/{vnc_port}"
    if not os.path.exists(tmp_interface_dir):
        os.makedirs(tmp_interface_dir)
    with open(f'{tmp_interface_dir}/interfaces', 'w') as f_w:
        f_w.write(int_eth0)
        return tmp_interface_dir


def interface_eth1_file(ip_addr, netmask, gateway, dns1, dns2, s_uuid):
    # ipaddr = "192.168.10.3"
    # netmask = "255.255.255.0"
    int_eth1 = f'''NAME=eth1
DEVICE=eth1
ONBOOT=yes
NETBOOT=yes
NM_CONTROLLED=no
IPV6INIT=yes
BOOTPROTO=static
TYPE=Ethernet
IPADDR={ip_addr}
NETMASK={netmask}
GATEWAY={gateway}
DNS1={dns1}
DNS2={dns2}'''
    with open(f'{tmp_interface}/{s_uuid}.txt', 'w') as f_w:
        f_w.write(int_eth1)


def centos_add_ip_system(ip_1, netmask_1, vnc_port, new_os_disk):
    tmp_interface_dir = interface_eth0_file(ip_1, netmask_1, vnc_port)
    subprocess.call(
        f"virt-copy-in  -a {new_os_disk}   {tmp_interface_dir}/ifcfg-eth0   /etc/sysconfig/network-scripts&&rm -rf {tmp_interface_dir}",
        shell=True)


def ubuntu_add_ip_system(ip_1, netmask_1, vnc_port, new_os_disk):
    tmp_interface_dir = u_interface_eth0_file(ip_1, netmask_1, vnc_port)
    subprocess.call(
        f"virt-copy-in  -a {new_os_disk}   {tmp_interface_dir}/interfaces   /etc/network&&rm -rf {tmp_interface_dir}",
        shell=True)
    subprocess.call(
        f"virt-copy-in  -a {new_os_disk}   {tmp_interface_dir}/interfaces   /etc/network&&rm -rf {tmp_interface_dir}",
        shell=True)


def save_install_info(vnc_port, server_name, server_mac, server_uuid, logger):
    virtual_info = f"{vnc_port},{server_name},{server_mac},{server_uuid}\n"
    with open(os_args_file, "a") as f:
        f.write(virtual_info)  # 保存虚拟机信息
    logger.debug(f"装机{server_name}成功了哦")
    return server_name, vnc_port


def create_new_os(mirror_name, cpu_num, memory_num, disk_size, eth0_ip=None, eth0_net=None):
    logger = logging.getLogger("new_install")
    bus = "virtio"
    template_os_disk_path = 20
    assert global_args_if()
    server_uuid, server_mac, vnc_port = create_xml_info()
    # logger.debug(f"{mirror_name}")
    os_version, state, template_os_disk = os_xml_disk.get_page_info(mirror_name)
    server_name = f"{os_version}-{state}-{vnc_port}"
    logger.debug(f"装机参数{server_name}, {server_uuid}, {server_mac}, {vnc_port}")
    memory_byte = int(memory_num) * 1024
    if "windows" in os_version:
        max_memory = int(memory_num)
    else:
        max_memory = 8 * 1024
    new_os_file = file_path + server_name + ".xml"
    new_os_disk = disk_path + server_name + ".qcow2"
    if "auto" in state:  # 自动安装
        if "client_auto" in state:  # 客户镜像自动安装
            os_version = mirror_name.split(".qcow2")[0]
            server_name = f"{os_version}-{vnc_port}"
            client_mirror = os_xml_disk.client_mirror_read_info()
            info = client_mirror[os_version]
            template_os_disk = info[0]
            template_os_disk_path = int(int(info[1]) / 1024 / 1024 / 1024)  # 单位是G
            new_os_file = file_path + server_name + ".xml"
            new_os_disk = disk_path + server_name + ".qcow2"
        try:
            if int(disk_size) >= int(template_os_disk_path):
                # subprocess.Popen(f"cp {template_os_file} {new_os_file}&&cp {template_os_disk} {new_os_disk}", shell=True)
                subprocess.check_call(
                    f"cp {template_os_file} {new_os_file}&&qemu-img create -f qcow2 -b {template_os_disk} {new_os_disk} {disk_size}G",
                    shell=True)
                if "centos" in os_version:
                    centos_add_ip_system(eth0_ip, eth0_net, vnc_port, new_os_disk)
                elif "ubuntu" in os_version:
                    ubuntu_add_ip_system(eth0_ip, eth0_net, vnc_port, new_os_disk)
                    pass
                elif "windows" in os_version:
                    pass
                # 1.定义虚拟机，2修改虚拟机内部配置，3启动机器，4保存虚拟机信息
                # 修改xml :  编辑名,name，uuid ,磁盘路径, mac (可能是两个)，vnc_端口
                with open(new_os_file, "r", ) as f_r:
                    infos = f_r.readlines()
                with open(new_os_file, "w") as f_w:
                    for line in infos:
                        if "virsh edit" in line:
                            line = f" virsh edit {server_name}\n"
                        if "<name>" in line:
                            line = f"<name>{server_name}</name>\n"
                        # if "dev='hda'" in line and "client" in state:
                        #     line = f"<target dev='vda' bus='ide'/>\n"
                        if "uuid" in line:
                            line = f"<uuid>{server_uuid}</uuid>\n"
                        if "<currentMemory unit='KiB'>" in line:
                            line = f"<currentMemory unit='KiB'>{memory_byte}</currentMemory>\n"
                        if "<memory unit='KiB'>" in line:
                            line = f"<memory unit='KiB'>{max_memory * 1024}</memory>\n"
                        if "<vcpu placement='static'" in line:
                            line = f"<vcpu placement='static' current='{cpu_num}'>32</vcpu>\n"
                        if "<source file" in line:
                            line = f"<source file='{new_os_disk}'/>\n"
                        if "<mac address" in line:
                            line = f"<mac address='{server_mac}'/>\n"
                        if "<graphics type='vnc'" in line:
                            line = f"<graphics type='vnc' port='{vnc_port}' autoport='no' listen='0.0.0.0'>\n"
                        f_w.write(line)
                subprocess.check_call(f"virsh define {new_os_file}", shell=True)
                subprocess.check_call(f"virsh start  {server_name}", shell=True)
                return save_install_info(vnc_port, server_name, server_mac, server_uuid, logger)
            logger.error(f"{server_name}磁盘空间设置要大于{template_os_disk_path}")
            return server_name, 1
        except Exception as e:
            subprocess.call(f"virsh undefine {server_name}", shell=True)
            subprocess.call(f"rm -f {new_os_file}&&rm -f {new_os_disk}", shell=True)
            print(e)
            logger.error(f"*{server_name}开启服务器失败*:{traceback.format_exc()}")
            return server_name, 2

    else:  # 手动安装
        try:
            subprocess.check_call(
                f"qemu-img   create  -f  qcow2 {new_os_disk}   {disk_size}G",
                shell=True)
            if "centos" in os_version and "ubuntu" in os_version:
                bus = "virtio"
            elif "windows" in os_version:
                bus = "ide"
            else:
                pass
            result = subprocess.check_call(
                f"virt-install --name={server_name} --metadata uuid={server_uuid} --os-variant=RHEL7 --memory={memory_num},maxmemory={max_memory} --vcpus={cpu_num},maxvcpus=32 --disk path={new_os_disk},format=qcow2,size={disk_size},bus={bus} --accelerate --cdrom {template_os_disk} --vnc --vncport={vnc_port} --vnclisten=0.0.0.0 --network bridge=br0,model=virtio,mac={server_mac} --noautoconsole",
                shell=True)
            if result == 0:
                return save_install_info(vnc_port, server_name, server_mac, server_uuid, logger)
        except Exception as e:
            subprocess.call(f"virsh undefine {server_name}", shell=True)
            subprocess.call(f"rm -f {new_os_file}&&rm -f {new_os_disk}", shell=True)
            print(e)
            logger.error(f"*{server_name}创建磁盘失败*:{traceback.format_exc()}")
            return server_name, 2


def reload_install_os(s_uuid, mirror_name, ip_1=None, netmask_1=None):
    """
    获取模板磁盘,获取本机源磁盘路径、大小
    @param s_uuid:
    @param mirror_name: 服务器
    @param ip_1:
    @param netmask_1:
    @return: True:成功   False:失败
    """
    logger = logging.getLogger("reload_install")
    try:
        with KVMHelp() as kvm_info:
            os_version, state, template_os_path = get_page_info(mirror_name)

            server_info = kvm_info.get_vir_info(s_uuid)
            if int(server_info["status"]):  # 强制关机
                kvm_info.power(s_uuid, "destroy")
            if "vda" in server_info['disk'].keys():  # 获取磁盘信息
                name, server_disk_path, server_disk_size = server_info['disk']['vda']
                disk_size_g = int(server_disk_size / 1024 / 1024 / 1024)
            server_name = server_info['name']
            vnc_port = server_info['vnc_port']
            subprocess.check_call(f"qemu-img create -f qcow2 -b {template_os_path} {server_disk_path} {disk_size_g}G",
                                  shell=True)
            if "centos" in os_version:
                centos_add_ip_system(ip_1, netmask_1, vnc_port, server_disk_path)
            elif "ubuntu" in os_version:
                ubuntu_add_ip_system(ip_1, netmask_1, vnc_port, server_disk_path)
            elif "windows" in os_version:
                pass
            subprocess.check_call(f"virsh start  {server_name}", shell=True)
            logger.debug(f"*{os_version}重装成功并开机*")
            return True
    except Exception as e:
        print(e)
        logger.error(f"*{os_version}重装失败*:{traceback.format_exc()})")
        return False


def make_exclusive_mirror(s_uuid, version_num):
    """
    制作镜像并保持镜像信息
    @param s_uuid:
    @param version_num:填写目前版本号 v1 ,v2
    @return:
    """
    logger = logging.getLogger("make_mirror_client")
    with KVMHelp() as kvm_info:
        server_info = kvm_info.get_vir_info(s_uuid)
        domain_name = server_info['name']
        client_mirror_name = f"{domain_name}-{version_num}"
        logger.debug(f"{client_mirror_name}准备开始拷贝镜像")
        try:
            if "hda" in server_info['disk'].keys():
                name, server_disk_path, server_disk_size = server_info['disk']['hda']
            if "vda" in server_info['disk'].keys():
                name, server_disk_path, server_disk_size = server_info['disk']['vda']
            xml_path = f"/etc/libvirt/qemu/{domain_name}.xml"
            if os.path.exists(xml_path) and os.path.exists(server_disk_path):
                client_template_disk_name = f"{client_mirror_name}.qcow2"
                client_template_disk_name_path = f"{client_template_dir}/{client_template_disk_name}"
                with open(client_template_mirror_storage_info, 'r') as f_r:
                    result = str(f_r.readlines())
                if re.findall(client_mirror_name, result):  # 已经存在改镜像名
                    return 3
                else:
                    subprocess.check_call(
                        f"cp {server_disk_path} {client_template_disk_name_path}",
                        shell=True)
                    with open(client_template_mirror_storage_info, 'a+') as f_w:
                        f_w.write(
                            f"{client_mirror_name},{client_template_disk_name_path},{server_disk_size}\n")
                logger.debug(f"{client_mirror_name}镜像制作完成")
                return 0
            return 1
        except Exception as e:
            print(e)
            logger.error(f"{client_mirror_name}镜像制作失败:{traceback.format_exc()}")
            return 2


def delete_manual_client_mirror(mirror_name):
    c_t_file = client_template_mirror_storage_info
    server_name = mirror_name.split('.qcow2')[0]
    client_mirror = os_xml_disk.client_mirror_read_info()
    try:
        mirror_path = client_mirror.get(server_name)[0]
    except Exception as e:
        print(e)
        return 1
    subprocess.Popen(f"rm -rf {mirror_path}", shell=True)
    with open(c_t_file, 'r') as f_r:
        result = f_r.readlines()
    with open(c_t_file, 'w')as f_w:
        for line in result:
            if mirror_name in line:
                continue
            f_w.write(line)
    return 0


if __name__ == "__main__":
    # mirror_name = "windows-12_server_2012_vl_x64_dvd_917962.iso"
    # cpu_num = 2
    # memory_num = 2048
    # disk_size = 40
    # method = "server"
    # create_new_os(mirror_name, cpu_num, memory_num, disk_size, method, eth0_ip=None, eth0_net=None)
    # s_uuid = "4a90fcfc-f666-11ea-8d7c-96520df980c4"
    # version_num = "v1"
    # make_exclusive_mirror(s_uuid, version_num)
    # mirror_name = "ubuntu14-manual-9702-v2.qcow2"
    # a = delete_manual_client_mirror(mirror_name)
    # print(a)
    pass
