#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    : 20/9/14 下午2:16
# @Author  : liaozz
# @File    : utils.py

"""
    自我介绍一下
"""

import json,traceback,os

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



if __name__ == "__main__":
    pass