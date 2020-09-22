#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import fnmatch
import os

template_dir = "/data/template"
original_iso = "/data/iso"
os_v_info = f"{template_dir}/os_info.json"
client_template_dir = "/data/client/template"
client_template_mirror_storage_info = "/data/client/mirror.json"

def checkout_evn(paths):
    for path in paths:
        path_array=path.split("/")
        path_str=""
        for p in path_array:
            if not "."  in p:
                path_str = path_str + "/" + p
                if not os.path.exists(path_str):
                    os.mkdir(path)
paths=[template_dir,original_iso,os_v_info,client_template_dir,client_template_mirror_storage_info]
checkout_evn(paths)


# centos7.4
# centos7.2
# centos7.0
# windows08
# windows12
# windoss16
# ubuntu14.4
# ubuntu16.4

def update_mirror_info():
    """
    """
    info = {}
    auto_os_config = {}
    manual_os_config = {}
    os_servers = ["centos6.5", "centos6.8", "centos7.0", "centos7.1", "centos7.2", "centos7.3", "centos7.4",
                  "windows08", "windows10", "windows12", "windows16", "ubuntu14", "ubuntu16"]
    for os_server in os_servers:
        os_disk = {}
        # os_xml = {}
        one_server_info = {}
        os_dir = f"{template_dir}/{os_server}"
        if os.path.exists(os_dir):
            os.chdir(os_dir)
            names = os.listdir('.')
            if names:
                list_disks = fnmatch.filter(names, '*.qcow2')
                os_disk_paths = []
                for list_disk in list_disks:
                    os_disk_paths.append(f"{os_dir}/{list_disk}")
                auto_os_config[os_server] = os_disk_paths
    info['auto'] = auto_os_config
    # 手动镜像
    os.chdir(original_iso)
    m_names = os.listdir('.')
    if m_names:
        mirrors_iso = fnmatch.filter(m_names, '*.iso')
        for mirror_name in os_servers:
            one_mirrors = []
            for name in mirrors_iso:
                file_name = f"{original_iso}/{name}"
                if mirror_name in name.lower() or mirror_name in ''.join(name.lower().split('-')):
                    one_mirrors.append(file_name)
                    manual_os_config[mirror_name] = one_mirrors
    info['manual'] = manual_os_config
    with open(os_v_info, "w") as f:
        f.write(json.dumps(info, indent=4))


def client_mirror_read_info():
    mirror_infos = {}
    if os.path.exists(client_template_mirror_storage_info):
        with open(client_template_mirror_storage_info, 'r') as f_r:
            client_mirror_info = f_r.readlines()
            for mirror in client_mirror_info:
                if mirror.strip():
                    mirror_name = mirror.strip().split(',')[0]
                    mirror_disk_path = mirror.strip().split(',')[1]
                    mirror_disk_size = mirror.strip().split(',')[2]
                    mirror_infos[mirror_name] = [mirror_disk_path, mirror_disk_size]
    return mirror_infos


def read_os_info():
    with open(os_v_info, 'r') as f_r:
        os_info = json.load(f_r)
    client_mirrors = client_mirror_read_info()
    print(client_mirrors)
    info = {}
    for client_name, client_values in client_mirrors.items():  # 将客户镜像也添加进来
        os_version = client_name
        client_path = [client_values[0]]
        info[os_version] = client_path
        os_info["client_auto"] = info
    return os_info


def read_mirror_list():
    update_mirror_info()
    all_mirror_name = []
    all_mirror_path = []
    os_info = read_os_info()
    one_mirror_list = [x for i in os_info.values() for x in i.values()]
    for y in one_mirror_list:
        all_mirror_path.extend(y)
    for z in all_mirror_path:
        all_mirror_name.append(z.strip().split("/")[-1])
    return all_mirror_name


def get_page_info(mirror_name):
    os_info = read_os_info()
    for status, values in os_info.items():
        for os_version, iso_paths in values.items():
            for path in iso_paths:
                if mirror_name in path:
                    return os_version, status, path


if __name__ == '__main__':
    update_mirror_info()
    # a = read_mirror_list()
    # print(a)
    # b = read_os_info()
    # print(b)
    c =client_mirror_read_info()
    print(c)
    pass
