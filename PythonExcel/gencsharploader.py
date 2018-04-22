#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-01-05 12:09:09
# @Author  : baronban (baronban@139.com)
# @Link    : 23578290.qq.com
# @Version : $Id$

import os
import argparse
import subprocess
import sys
from string import Template
import hashlib

# prefix
FILE_PREFIX = "mmo3d_"

class CSharpLoaderGen:
    "生成加载protobuf的csharp代码"
    pbnamelist=[]
    templatepath='.\\template'
    opath=""
    csharpcontent=[
        'using System.Collections;',
        'using System.Collections.Generic;',
        'using protos;'
    ]

    def initenv(self,configlist,outputpath,protopath):

        self.pbnamelist=configlist

        self.opath = outputpath

        self.protopath = protopath

    def genCSharp(self):
        lff = open(self.templatepath+'\\TableDataReader.cs.tpl')
        loadfunctiontemplate = lff.read()
        lff.close()
        loadfunctionlines=[]

        for name in self.pbnamelist:
            md5file=open(self.protopath + FILE_PREFIX + name.lower() + ".proto",'rb')
            if md5file:
                cur_md5=hashlib.md5(md5file.read()).hexdigest()
                md5file.close()
            else:
                cur_md5=""

            ld = {'pbname':name,'pbnamelowercase':name.lower(),"protomd5":cur_md5.lower()}
            ltt = Template(loadfunctiontemplate)
            loadfunctionlines.append(ltt.substitute(ld))
        self.csharpcontent.extend(loadfunctionlines)
        cppfc = open(self.opath+'\\TableDataReader.cs','w')
        cppfc.write('\n'.join(self.csharpcontent))
        cppfc.close()


if __name__=="__main__":
    b_parser = argparse.ArgumentParser(description='Hello')
    b_parser.add_argument('pbcpath',help='protobuf config path')
    b_parser.add_argument('outputpath',help='protobuf csharp loader output path')
    b_parser.add_argument('protodir',help="data file output dir path ")
    
    b_args = b_parser.parse_args()
    configlist =[]
    cf = open(b_args.pbcpath,'r')
    for line in cf:
        configlist.append(line.split(' ')[0])
    cf.close()
    
    clg = CSharpLoaderGen()
    clg.initenv(configlist,b_args.outputpath,b_args.protodir)
    clg.genCSharp()