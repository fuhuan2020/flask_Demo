#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    : 20/7/31 上午9:37
# @Author  : liaozz
# @File    : tests.py

"""
    自我介绍一下
"""

import requests, json, os, os_xml_disk

URL = "http://192.168.88.87:8008/kvm"


# URL = "http://192.168.66.22:8001/kvm"

# URL = "http://192.168.88.87:10000/kvm"


def post_request(data_dict):
    '''
    通用方法
    :param data_dict:
    :return:
    '''
    result_dict = None
    da = data_dict
    result = requests.post(URL, data=da)
    if result and result.status_code == 200:
        try:
            result_dict = json.loads(result.content)
        except Exception as e:
            print("解析错误")
            print(result.content)

        pass
    elif result:
        print(result.status_code)
    else:
        print("未知错误")
    return result_dict


def test_create():
    da = dict(js="create", os_version="centos74", cpu_num="1", memory_num="1", disk_size="20")
    result_dict = post_request(da)
    if result_dict:
        print(json.dumps(result_dict, indent=4))
    pass


def test_delete():
    da = dict(js="delete", bb=22)
    result_dict = post_request(da)
    if result_dict:
        print(json.dumps(result_dict, indent=4))
    pass


def test_get_info():
    da = dict(js="kvm_info", bb=22)
    result_dict = post_request(da)
    if result_dict:
        print(json.dumps(result_dict, indent=4))
    pass


def test_power():
    da = dict(js="kuaiz", uuid="5e16d4b9-2306-4ec4-a981-050c69308f1f", )
    result_dict = post_request(da)
    if result_dict:
        print(json.dumps(result_dict, indent=4))
    pass


def test_xml():
    aa = '''<domain type='kvm'>\n  <name>u12-templat-6002-clean1</name>\n  <uuid>789b96d9-8010-4c28-becb-98fcf6555afc</uuid>\n  <memory unit='KiB'>524288</memory>\n  <currentMemory unit='KiB'>524288</currentMemory>\n  <vcpu placement='static'>1</vcpu>\n  <os>\n    <type arch='x86_64' machine='pc-i440fx-rhel7.0.0'>hvm</type>\n    <boot dev='hd'/>\n  </os>\n  <features>\n    <acpi/>\n    <apic/>\n  </features>\n  <cpu mode='custom' match='exact' check='partial'>\n    <model fallback='allow'>Haswell-noTSX-IBRS</model>\n    <feature policy='require' name='spec-ctrl'/>\n    <feature policy='require' name='ssbd'/>\n  </cpu>\n  <clock offset='utc'>\n    <timer name='rtc' tickpolicy='catchup'/>\n    <timer name='pit' tickpolicy='delay'/>\n    <timer name='hpet' present='no'/>\n  </clock>\n  <on_poweroff>destroy</on_poweroff>\n  <on_reboot>restart</on_reboot>\n  <on_crash>destroy</on_crash>\n  <pm>\n    <suspend-to-mem enabled='no'/>\n    <suspend-to-disk enabled='no'/>\n  </pm>\n  <devices>\n    <emulator>/usr/libexec/qemu-kvm</emulator>\n    <disk type='file' device='disk'>\n      <driver name='qemu' type='qcow2'/>\n      <source file='/data/kvm/u12-templat-6002-clean1.qcow2'/>\n      <target dev='vda' bus='virtio'/>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>\n    </disk>\n    <disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <target dev='hda' bus='ide'/>\n      <readonly/>\n      <address type='drive' controller='0' bus='0' target='0' unit='0'/>\n    </disk>\n    <controller type='usb' index='0' model='ich9-ehci1'>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x7'/>\n    </controller>\n    <controller type='usb' index='0' model='ich9-uhci1'>\n      <master startport='0'/>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0' multifunction='on'/>\n    </controller>\n    <controller type='usb' index='0' model='ich9-uhci2'>\n      <master startport='2'/>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x1'/>\n    </controller>\n    <controller type='usb' index='0' model='ich9-uhci3'>\n      <master startport='4'/>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x2'/>\n    </controller>\n    <controller type='pci' index='0' model='pci-root'/>\n    <controller type='ide' index='0'>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>\n    </controller>\n    <interface type='bridge'>\n      <mac address='52:54:00:f6:1c:2d'/>\n      <source bridge='br0'/>\n      <model type='virtio'/>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>\n    </interface>\n    <serial type='pty'>\n      <target type='isa-serial' port='0'>\n        <model name='isa-serial'/>\n      </target>\n    </serial>\n    <console type='pty'>\n      <target type='serial' port='0'/>\n    </console>\n    <input type='tablet' bus='usb'>\n      <address type='usb' bus='0' port='1'/>\n    </input>\n    <input type='mouse' bus='ps2'/>\n    <input type='keyboard' bus='ps2'/>\n    <graphics type='vnc' port='6002' autoport='no' listen='0.0.0.0'>\n      <listen type='address' address='0.0.0.0'/>\n    </graphics>\n    <video>\n      <model type='cirrus' vram='16384' heads='1' primary='yes'/>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>\n    </video>\n    <memballoon model='virtio'>\n      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>\n    </memballoon>\n  </devices>\n</domain>'''

    bb = aa.replace("\n", "")
    import xml.dom.minidom as xmldom

    xml_obj = xmldom.parseString(aa)
    name = xml_obj.getElementsByTagName("name")[0].firstChild.data
    source_name = xml_obj.getElementsByTagName("source")[0].getAttribute("file")
    port = xml_obj.getElementsByTagName("graphics")[0].getAttribute("port")
    mac_element = xml_obj.getElementsByTagName("mac")
    macs = ",".join(i.getAttribute("address") for i in mac_element)


def get_vnc_token_str():
    path = "/var/noVNC/utils/websockify/token.conf"
    conten = ""
    if os.path.exists(path):
        try:
            with open(path) as token:
                lines = token.readlines()
                conten = "".join(item for item in lines)
        except Exception as e:
            pass
    print(conten)

    pass


def may_install_system():
    '''
    获取可安装的系统版本
    @return:
    返回系统版本例如：centos7.4  windows12
    '''
    system_version = os_xml_disk.read_value()
    return system_version


if __name__ == "__main__":
    # test_create()
    # test_delete()
    # test_get_info()
    # test_power()
    # get_vnc_token_str()
    # may_install_system()
    # aa={"12":"ww","13":"ww","14":"ww","15":"ww"}
    # bb=aa.keys()
    # cc=(",".join(item for item in bb)).split(",")
    # print(cc)
    # pass
    import math

    print(16 * math.pow(1.05, 8))
    print(28 * 1.1 * 1.1)
    test = {"a": 1, "b": 2}
    print(test.get("a"))
    print(test.get("c", 10))
    print(test.get("d"))
