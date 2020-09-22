#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import libvirt
#
# with libvirt.open('qemu:///system') as f:
#     xml = "/etc/libvirt/qemu/centos7.4-test-9997.xml"
#     print(f.listAllNetworks())

import functools
import inspect


def check_is_admin(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        func_args = inspect.getcallargs(f, *args, **kwargs)
        print(func_args)
        if func_args.get('username') != 'admin':
            raise Exception("This user is not allowed to get food")
        return f(*args, **kwargs)

    return wrapper


@check_is_admin
def get_food(username, food='chocolate'):
    return "{0} get food: {1}".format(username, food)


def main():
    print(get_food('admin'))


def aaa(method):
    if "server" in method.keys():
        print("abcdddd")
    # print(method.keys())
    pass


if __name__ == '__main__':
    # import time
    #
    # a = time.clock()
    # time.sleep(1)
    # print(time.clock() - a)
    # main()
    #

    method = {"server": "auto"}
    aaa(method)
