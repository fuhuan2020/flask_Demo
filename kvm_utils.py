#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    : 20/7/31 上午10:58
# @Author  : liaozz
# @File    : kvm_utils.py

"""
    自我介绍一下
"""
import sys, os, traceback, time
import xml.dom.minidom as xmldom
from xml.etree import ElementTree
from my_crontab import get_ip_from_mac

try:
    import libvirt

    HAS_LIBVIRT = True
except Exception:
    HAS_LIBVIRT = False


class KVMHelp(object):
    conn = None

    def __init__(self):
        self.conn = self.__get_conn()
        pass

    def is_virtual(self):
        '''
        判断当前系统是否支持KVM虚拟化,不支持则退出
        '''
        if not HAS_LIBVIRT:
            sys.exit("current system are not support Virtualization")
        return 'virt'

    def __get_conn(self):
        '''
        获取libvirt的连接句柄,用于提供操作libivrt的接口
        '''
        conn = None
        if self.is_virtual() == 'virt':
            try:
                conn = libvirt.open('qemu:///system')
            except Exception as e:
                traceback.print_exc()

        return conn

    def close_conn(self):
        '''
        关闭libvirt的连接句柄
        '''
        if self.conn:
            return self.conn.close()
        return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            self.conn = None
        pass

    def __enter__(self):
        return self

    def list_active_vms(self):
        '''
        获取所有开机状态的instance,返回虚拟机的名字
        '''
        vms_list = []
        if self.conn:
            domain_list = self.conn.listDomainsID()
            for id in domain_list:
                vms_list.append(self.conn.lookupByID(id).name())
        return vms_list

    def list_inactive_vms(self):
        '''
        获取关机状态的instance，返回虚拟机的名字
        '''
        vms_list = []
        if self.conn:
            for id in self.conn.listDefinedDomains():
                vms_list.append(id)
        return vms_list

    def list_all_vms(self):
        '''
        获取所有的虚拟机
        '''
        vms = []
        vms.extend(self.list_active_vms())
        vms.extend(self.list_inactive_vms())
        return vms

    def power(self, uuid, action):
        flag = False
        if self.conn:
            flag = True
            list_all_domain = self.conn.listAllDomains()
            for domain in list_all_domain:
                if domain.UUIDString() == uuid:
                    if action == "start":
                        if str(domain.isActive()) == "0":
                            os.popen("virsh start %s" % domain.name())
                    elif action == "stop":
                        if str(domain.isActive()) == "1":
                            domain.shutdown()
                    elif action == "reboot":
                        if str(domain.isActive()) == "1":
                            domain.reboot()
                    elif action == "destroy":
                        if str(domain.isActive()) == "1":
                            domain.destroy()
                    elif action == "undefine":
                        if str(domain.isActive()) == "0":
                            result = domain.undefine()
                            return result
                    else:
                        flag = False
                pass
        return flag

        pass

    def get_kvm_info(self):
        info_list = []
        if self.conn:
            listAllDomains = self.conn.listAllDomains()
            for i, domain in enumerate(listAllDomains):
                id = i
                name = domain.name()
                status = domain.isActive()
                uuid = domain.UUIDString()
                memory = domain.info()[2]
                cpu = domain.info()[3]
                xml_desc = domain.XMLDesc()
                xml_obj = xmldom.parseString(xml_desc)
                source_path = xml_obj.getElementsByTagName("source")[0].getAttribute("file")
                port = xml_obj.getElementsByTagName("graphics")[0].getAttribute("port")
                mac_element = xml_obj.getElementsByTagName("mac")
                macs = ",".join(i.getAttribute("address") for i in mac_element)
                ips=get_ip_from_mac(macs)
                info_dict = dict(id=str(i), name=name, status=status, uuid=uuid, memory=memory, cpu=cpu,
                                 source_path=source_path, port=port, macs=macs,ips=ips)
                info_list.append(info_dict)
        return info_list

    def get_capability(self):
        '''
        得到hypervisor的容量信息,返回格式为XML
        '''
        capability = None
        if self.conn:
            capability = self.conn.getCapabilities()
        return capability

    def get_hostname(self):
        '''
        attain hypervisor's hostname
        '''
        hostname = None
        if self.conn:
            hostname = self.conn.getHostname()
        return hostname

    def get_max_vcpus(self):
        """
        获取hypervisor支持虚拟机的最大CPU数
        """
        max_vcpus = None
        if self.conn:
            max_vcpus = self.conn.getMaxVcpus(None)
        return max_vcpus

    def get_hypervisor_cpu_num(self):
        if self.conn:
            nodeinfo = self.conn.getInfo()
            # print('Model: ' + str(nodeinfo[0]))
            # print('Memory size: ' + str(nodeinfo[1]) + 'MB')
            # print('Number of CPUs: ' + str(nodeinfo[2]))
            # print('MHz of CPUs: ' + str(nodeinfo[3]))
            # print('Number of NUMA nodes: ' + str(nodeinfo[4]))
            # print('Number of CPU sockets: ' + str(nodeinfo[5]))
            # print('Number of CPU cores per socket: ' + str(nodeinfo[6]))
            # print('Number of CPU threads per core: ' + str(nodeinfo[7]))
            cpu_num = nodeinfo[2]
            return cpu_num
            pass

    def get_hypervisor_memory_size(self):
        """
        单位是MB
        @return:
        """
        if self.conn:
            nodeinfo = self.conn.getInfo()
            memory_size = nodeinfo[1]
            return memory_size

    def get_cell_free_memory_list(self):
        if self.conn:
            nodeinfo = self.conn.getInfo()
            numnodes = nodeinfo[4]
            memlist = self.conn.getCellsFreeMemory(0, numnodes)
            # cell=0
            # for cellfreemem in memlist:
            #     print('Node ' + str(cell) + ': ' + str(cellfreemem) + ' bytes free memory')
            #     cell += 1
            # pass
            return memlist

    def get_hy_memory_list(self):
        if self.conn:
            memory_list = self.conn.getMemoryStats(libvirt.VIR_NODE_MEMORY_STATS_ALL_CELLS)
            return memory_list

    def set_cpu(self, dom_name, cpu_num):
        """
        @param dom_name:
        @param cpu_num: 1,2 正整数
        @return:
        """
        if self.conn:
            dom = self.conn.lookupByName(dom_name)
            if dom.isActive():
                current_cpu = dom.info()[3]
                if cpu_num > current_cpu:
                    dom.setVcpusFlags(cpu_num, 1)  # 在线添加
                    dom.setVcpusFlags(cpu_num, 2)  # 配置文件添加
                    return 0
                else:
                    return 1
            dom.setVcpusFlags(cpu_num, 0)  # 关机添加
            return 0

    def set_memory(self, dom_name, memory_num):
        """
        @param dom_name:
        @param memory_num: 单位KB 1GB=1024*1024KB
        @return:
        """
        if self.conn:
            dom = self.conn.lookupByName(dom_name)
            if dom.isActive():
                current_memory = dom.info()[2]
                if memory_num > current_memory:
                    dom.setMemoryFlags(memory_num, 1)  # 在线添加
                    dom.setMemoryFlags(memory_num, 2)  # 配置文件添加
                    return 0
                else:
                    return 1
            dom.setMemoryFlags(memory_num, 0)  # 关机添加
            return 0
        pass

    def get_vir_info(self, uuid):
        """
        @param uuid:
        @return: name,status,uuid,memory,max_memory,cpu,max_cpu,vnc_port,interface{},disk{},
        """
        interface = {}
        disk = {}
        if self.conn:
            listAllDomains = self.conn.listAllDomains()
            for i, domain in enumerate(listAllDomains):
                if uuid == domain.UUIDString():
                    name = domain.name()
                    status = domain.isActive()
                    max_memory = domain.info()[1]
                    memory = domain.info()[2]
                    cpu = domain.info()[3]
                    tree = ElementTree.fromstring(domain.XMLDesc())
                    max_cpu = tree.findall('vcpu')[0].text
                    # print(domain.XMLDesc())
                    interface_objects = tree.findall('devices/interface')
                    for interface_object in interface_objects:
                        mac = interface_object.find('mac').get('address')
                        bridge = interface_object.find('source').get('bridge')
                        interface[bridge] = bridge, mac
                    disk_objects = tree.findall('devices/disk')
                    for disk_object in disk_objects:
                        if disk_object.get('device') == 'disk':
                            block_path = disk_object.find('source').get('file')
                            block_name = disk_object.find('target').get('dev')
                            block_size = domain.blockInfo(block_path)[0]
                            disk[block_name] = block_name, block_path, block_size
                    vnc_port = tree.findall('devices/graphics')[0].get('port')
                    vir_info = dict(name=name, status=status, uuid=uuid, memory=memory, max_memory=max_memory,
                                    cpu=cpu, max_cup=max_cpu, vnc_port=vnc_port, interface=interface, disk=disk)
                    return vir_info

    # 虚拟机磁盘io情况
    def get_vir_disk_io(self, interval_time, dom_name):
        """
        @param dom_name:
        @return: key:块（vda）  rd_req_percent, rd_bytes_percent, wr_req_percent, wr_bytes_percent
        """
        if self.conn:
            info = {}
            dom = self.conn.lookupByName(dom_name)
            if dom.isActive():
                tree = ElementTree.fromstring(dom.XMLDesc())
                disk_objects = tree.findall('devices/disk')
                for disk_object in disk_objects:
                    if disk_object.get('device') == 'disk':
                        block_path = disk_object.find('source').get('file')
                        block_name = disk_object.find('target').get('dev')
                        stats_1 = dom.blockStats(block_path)
                        rd_req_1 = stats_1[0]
                        rd_bytes_1 = stats_1[1]
                        wr_req_1 = stats_1[2]
                        wr_bytes_1 = stats_1[3]
                        time.sleep(interval_time)
                        stats_2 = dom.blockStats(block_path)
                        rd_req_2 = stats_2[0]
                        rd_bytes_2 = stats_2[1]
                        wr_req_2 = stats_2[2]
                        wr_bytes_2 = stats_2[3]
                        rd_req_percent = float('%.1f' % float(rd_req_2 - rd_req_1))
                        rd_bytes_percent = float('%.2f' % float(rd_bytes_2 - rd_bytes_1))
                        wr_req_percent = float('%.1f' % float(wr_req_2 - wr_req_1))
                        wr_bytes_percent = float('%.2f' % float(wr_bytes_2 - wr_bytes_1))

                        info[block_name] = rd_req_percent, rd_bytes_percent, wr_req_percent, wr_bytes_percent
                return info

    # 虚拟机网卡接受和发送
    def get_vir_interface_info(self, interval_time, dom_name):
        '''
        @param interval_time:间隔时间
        @param dom_name:
        stats: key:桥 value：read bytes，read packets，read errors，read drops，
        write bytes，write packets，write errors，write drops
        @return:
        '''
        if self.conn:
            bridge_iface_info = {}
            dom = self.conn.lookupByName(dom_name)
            if dom.isActive():
                tree = ElementTree.fromstring(dom.XMLDesc())
                interface_objects = tree.findall('devices/interface')
                for interface_object in interface_objects:
                    mac = interface_object.find('mac').get('address')
                    bridge = interface_object.find('source').get('bridge')
                    iface = interface_object.find('target').get('dev')
                    stats1 = dom.interfaceStats(iface)
                    read_bytes_1 = stats1[0]
                    read_packets_1 = stats1[1]
                    write_bytes_1 = stats1[4]
                    write_packets_1 = stats1[5]
                    time.sleep(interval_time)
                    stats2 = dom.interfaceStats(iface)
                    read_bytes_2 = stats2[0]
                    read_packets_2 = stats2[1]
                    write_bytes_2 = stats2[4]
                    write_packets_2 = stats2[5]
                    receive_bytes_percent = float('%.2f' % float((read_bytes_2 - read_bytes_1) / interval_time))
                    receive_packets = read_packets_2 - read_packets_1
                    send_bytes_percent = float('%.2f' % float((write_bytes_2 - write_bytes_1) / interval_time))
                    send_packets = write_packets_2 - write_packets_1

                    bridge_iface_info[bridge] = receive_bytes_percent, send_bytes_percent
                return bridge_iface_info

    # 虚拟机cpu使用百分比
    def get_vir_cpu_percent(self, interval_time, dom_name):
        '''
        @param interval_time:
        @param dom_name:
        @return: 使用百分比
        '''
        if self.conn:
            dom = self.conn.lookupByName(dom_name)
            if dom.isActive():
                t1 = time.time()
                c1 = int(dom.info()[4])
                time.sleep(interval_time)
                t2 = time.time()
                c2 = int(dom.info()[4])
                c_nums = int(dom.info()[3])
                usage = (c2 - c1) * 100 / ((t2 - t1) * c_nums * 1e9)
                return usage

    # 虚拟机内存空闲
    def get_vir_memory_percent(self, dom_name):
        '''
        @param dom_name:
        @return: 未使用，可以获取
        '''
        if self.conn:
            dom = self.conn.lookupByName(dom_name)
            if dom.isActive():
                status = dom.memoryStats()
                unused = status['unused']
                available = status['available']
                actual = status['actual']

                unused_percent = float('%.2f' % float(unused / actual * 100))
                available_percent = float('%.2f' % float(available / actual * 100))
                return unused_percent, available_percent


if __name__ == "__main__":
    with KVMHelp() as kvm:
        # domName = 'centos7.4-test-9363'
        # dom = kvm.conn.lookupByName(domName)
        # a = dom.blockInfo('/data/kvm/centos7.4-test-9363.qcow2')
        # b = dom.blockJobAbort('/data/kvm/centos7.4-test-9363.qcow2')
        # print(a[0] / 1024 / 1024 / 1024)
        # print(a[1] / 1024 / 1024 / 1024)
        # print(a[2] / 1024 / 1024 / 1024)
        # cpu = dom.info()
        # print(a)
        # print(cpu)
        # uuid = "98452298-ed97-11ea-8d56-96520df980c4"
        # domname = 'centos7.4-test-9293'
        # # cpu_num = 4
        # # memory_num = 3 * 1024 * 1024
        # # kvm.set_memory(dom_name, memory_num)
        # # kvm.set_cpu(dom_name, cpu_num)
        # a = kvm.get_vir_info(uuid)
        # print(a)
        # istAllDomains = kvm.conn.listAllDomains()
        # print(istAllDomains)
        uuid_1 = "aebd2436-f237-11ea-8e31-96520df980c4"
        b = kvm.get_vir_info(uuid_1)
        print(b)
        name_1 = "windows12-m-test-9394"
        # a = kvm.set_cpu(name_1, 3)
        # print(a)
        # a = kvm.set_memory(name_1, 3 * 1024 * 1024)
        # print(a)
        # c = kvm.set_cpu(name_1, 4)
        # print(c)
        pass
