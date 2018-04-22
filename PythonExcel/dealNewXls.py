import os
import os.path
import argparse
import subprocess
import sys

import xlrd # for read excel

rootdir = "xlsData"

import xls_deploy_tool as xdt

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

if __name__=="__main__":
    b_parser = argparse.ArgumentParser(description='Make proto data from list.')
    b_parser.add_argument('-otype',choices=['proto','data'],help='output only proto or data,if not set ,output both')
    b_parser.add_argument('-odatadir',default="" ,help="data file output dir path ")
    b_parser.add_argument('-oprotodir',default="",help="proto file output dir path ")
    b_parser.add_argument('-otxtdir',default="",help="txt file contains data content output dir path ")
    b_parser.add_argument('-ocsharpdir',default="",help="csharp file contains define content output dir path ")
    
    b_args = b_parser.parse_args()

newsheets=[]
for parent, dirnames, filenames in os.walk(rootdir):  # 三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
    for filename in filenames:  # 输出文件信息
        print("parent is:" + parent)
        print("filename is:" + filename)
        fullfile = os.path.join(parent, filename)
        print("the full name of the file is:" + fullfile)  #输出文件路径信息

        if filename.endswith("xlsx") and not filename.startswith("~"):
	        bk = xlrd.open_workbook(fullfile)
	        for sheetname in bk.sheets():
	            print(sheetname.name)
	            if not check_contain_chinese(sheetname.name):
	            	try:
	            		xdt.mainprocess(sheetname.name,fullfile,b_args)
	            		temp = {}
	            		temp["name"] = sheetname.name
	            		temp["filename"] = filename
	            		newsheets.append(temp)
	            	except Exception as e:
	            		print(e)
	            	else:
	            		pass
	            	finally:
	            		pass



pbnamelist = []
cf = open("protolist.txt",'r')
for line in cf:
    pbnamelist.append(line.split(' ')[0])
cf.close()

cf = open("protolist.txt",'a')
for newsheet in newsheets:
	if newsheet["name"] not in pbnamelist:
		cf.write("\n"+newsheet["name"]+" "+newsheet["filename"])
cf.close()


	            	

