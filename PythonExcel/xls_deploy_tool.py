#! /usr/bin/env python
#coding=utf-8

##
# @file:   xls_deploy_tool.py(python3)
# @author: jameyli <lgy AT live DOT com>
# @modified by Eam at 2018.03.31
# @brief:  xls 配置导表工具

# 主要功能：
#     1 配置定义生成，根据excel 自动生成配置的PB定义
#     2 配置数据导入，将配置数据生成PB的序列化后的二进制数据或者文本数据
#
# 说明:
#   1 excel 的前四行用于结构定义, 其余则为数据，按第一行区分, 分别解释：
#       required 必有属性
#       optional 可选属性
#           第二行: 属性类型
#           第三行：属性名
#           第四行：注释
#           数据行：属性值
#       repeated 表明下一个属性是repeated,即数组
#           第二行: repeat的最大次数, excel中会重复列出该属性
#           2011-11-29 做了修改 第二行如果是类型定义的话，则表明该列是repeated
#           但是目前只支持整形
#           第三行：无用
#           第四行：注释
#           数据行：实际的重复次数
#       required_struct 必选结构属性
#       optional_struct 可选结构属性
#           第二行：结构元素个数
#           第三行：结构名
#           第四行：在上层结构中的属性名
#           数据行：不用填

#    1  | required/optional | repeated  | required_struct/optional_struct   |
#       | ------------------| ---------:| ---------------------------------:|
#    2  | 属性类型          |           | 结构元素个数                      |
#    3  | 属性名            |           | 结构类型名                        |
#    4  | 注释说明          |           | 在上层结构中的属性名              |
#    5  | 属性值            |           |                                   |

#
#
# 开始设计的很理想，希望配置定义和配置数据保持一致,使用同一个excel
# 不知道能否实现
#
# 功能基本实现，并验证过可以通过CPP解析 ohye
#
# 2011-06-17 修改:
#   表名sheet_name 使用大写
#   结构定义使用大写加下划线
# 2011-06-20 修改bug:
#   excel命名中存在空格
#   repeated_num = 0 时的情况
# 2011-11-24 添加功能
#   默认值
# 2011-11-29 添加功能
# repeated 第二行如果是类型定义的话，则表明该列是repeated
# 但是目前只支持整形

# TODO::
# 1 时间配置人性化
# 2 区分server/client 配置
# 3 repeated 优化
# 4 struct 优化

# 依赖:
# 1 protobuf
# 2 xlrd
##


import xlrd # for read excel
import sys
import os
import json
import argparse
import subprocess
import hashlib

# TAP的空格数
TAP_BLANK_NUM = 4

FIELD_RULE_ROW = 0
# 这一行还表示重复的最大个数，或结构体元素数
FIELD_TYPE_ROW = 1
FIELD_NAME_ROW = 2
FIELD_COMMENT_ROW = 3

# prefix
FILE_PREFIX = "mmo3d_"

#加密
GEN_CHECK_MD5 = True
CHECK_MD5_HEAD = "Mpd"
cur_md5 = ""

# output dir


def printeverylines(mylist,prefix='bc'):
    for l in mylist:
        print(prefix+':'+l)

def execommand(svnargcs,errfunc=printeverylines,outputfunc=printeverylines,baronenv=None,baroncwd=None):
    sc_popen = subprocess.Popen(svnargcs,stdout = subprocess.PIPE , stderr=subprocess.PIPE, universal_newlines=True,env=baronenv,cwd=baroncwd)
    sc_stdout,sc_stderr = sc_popen.communicate()
    if (sc_stderr):
        errfunc(sc_stderr.split('\n'))
    if(sc_stdout):
        outputfunc(sc_stdout.split('\n'))
    sc_returncode = sc_popen.poll()
    if(sc_returncode>0):
        print("Error Command:"+(' '.join(svnargcs) if isinstance(svnargcs,list) else svnargcs))
        raise
    return (sc_stdout,sc_stderr)

class LogHelp :
    """日志辅助类"""
    _logger = None
    _close_imme = True

    @staticmethod
    def set_close_flag(flag):
        LogHelp._close_imme = flag

    @staticmethod
    def _initlog():
        import logging

        LogHelp._logger = logging.getLogger()
        logfile = 'tnt_comm_deploy_tool.log'
        hdlr = logging.FileHandler(logfile)
        formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(lineno)d|%(funcName)s|%(message)s')
        hdlr.setFormatter(formatter)
        LogHelp._logger.addHandler(hdlr)
        #LogHelp._logger.setLevel(logging.NOTSET)
        LogHelp._logger.setLevel(logging.WARNING)

        LogHelp._logger.info("\n\n\n")
        LogHelp._logger.info("logger is inited!")

    @staticmethod
    def get_logger() :
        if LogHelp._logger is None :
            LogHelp._initlog()

        return LogHelp._logger

    @staticmethod
    def close() :
        if LogHelp._close_imme:
            import logging
            if LogHelp._logger is None :
                return
            logging.shutdown()

# log macro
#LOG_DEBUG=LogHelp.get_logger().debug
#LOG_INFO=LogHelp.get_logger().info
LOG_WARN=LogHelp.get_logger().warn
LOG_ERROR=LogHelp.get_logger().error


class SheetInterpreter:
    """通过excel配置生成配置的protobuf定义文件"""
    DIR_OUTPUT_PROTO = ""
    DIR_OUTPUT_CSHARP = ""
    def __init__(self, xls_file_path, sheet_name ,b_args):
        self._xls_file_path = xls_file_path
        self._sheet_name = sheet_name        
        self.DIR_OUTPUT_PROTO = b_args.oprotodir
        self.DIR_OUTPUT_CSHARP = b_args.ocsharpdir
        try:
            self._workbook = xlrd.open_workbook(self._xls_file_path)
        except Exception as e:
            print ("open xls file(%s) failed!" %(self._xls_file_path))
            raise

        try :
            self._sheet =self._workbook.sheet_by_name(self._sheet_name)
        except Exception as e:
            print ("open xls(%s) sheet(%s) failed!" %(self._xls_file_path,self._sheet_name))

        # 行数和列数
        self._row_count = len(self._sheet.col_values(0))
        self._col_count = len(self._sheet.row_values(0))

        self._row = 0
        self._col = 0

        # 将所有的输出先写到一个list， 最后统一写到文件
        self._output = []
        # 排版缩进空格数
        self._indentation = 0
        # field number 结构嵌套时使用列表
        # 新增一个结构，行增一个元素，结构定义完成后弹出
        self._field_index_list = [1]
        # 当前行是否输出，避免相同结构重复定义
        self._is_layout = True
        # 保存所有结构的名字
        self._struct_name_list = []

        self._pb_file_name = FILE_PREFIX + sheet_name.lower() + ".proto"

        print("SheetInterpreter.__init__ ok")

    def Interpreter(self) :
        #写proto文件
        """对外的接口"""
        #LOG_INFO("begin Interpreter, row_count = %d, col_count = %d", self._row_count, self._col_count)

        self._LayoutFileHeader()

        self._output.append("\npackage protos;")

        self._LayoutStructHead(self._sheet_name)
        self._IncreaseIndentation()

        while self._col < self._col_count :
            self._FieldDefine(0)

        self._DecreaseIndentation()
        self._LayoutStructTail()

        self._LayoutArray()

        self._Write2File()

        LogHelp.close()
        # 将PB转换成py格式
        try :
            command = "protoc --python_out=./ --proto_path="+self.DIR_OUTPUT_PROTO +" "+self.DIR_OUTPUT_PROTO + self._pb_file_name
            print("commad:"+command)
            os.system(command)
        except BaseException as e:
            print ("protoc or protogen failed!")
            raise

    def _FieldDefine(self, repeated_num) :
        #LOG_INFO("row=%d, col=%d, repeated_num=%d", self._row, self._col, repeated_num)
        field_rule = str(self._sheet.cell_value(FIELD_RULE_ROW, self._col))

        if field_rule == "required" or field_rule == "optional" :
            field_type = str(self._sheet.cell_value(FIELD_TYPE_ROW, self._col)).strip()
            field_name = str(self._sheet.cell_value(FIELD_NAME_ROW, self._col)).strip()
            field_comment = str(self._sheet.cell_value(FIELD_COMMENT_ROW, self._col)) # unicode 

            #LOG_INFO("%s|%s|%s|%s", field_rule, field_type, field_name, field_comment)

            comment = str(field_comment.encode("utf-8"))
            self._LayoutComment(comment)

            if repeated_num >= 1:
                field_rule = "repeated"

            self._LayoutOneField(field_rule, field_type, field_name)

            actual_repeated_num = 1 if (repeated_num == 0) else repeated_num
            self._col += actual_repeated_num

        elif field_rule == "repeated" :
            # 2011-11-29 修改
            # 若repeated第二行是类型定义，则表示当前字段是repeated，并且数据在单列用分好相隔
            second_row = str(self._sheet.cell_value(FIELD_TYPE_ROW, self._col)).strip()
            #LOG_DEBUG("repeated|%s", second_row);
            # exel有可能有小数点
            if second_row.isdigit() or second_row.find(".") != -1 :
                # 这里后面一般会是一个结构体
                repeated_num = int(float(second_row))
                #LOG_INFO("%s|%d", field_rule, repeated_num)
                self._col += 1
                self._FieldDefine(repeated_num)
            else :
                # 一般是简单的单字段，数值用分号相隔
                field_type = second_row
                field_name = str(self._sheet.cell_value(FIELD_NAME_ROW, self._col)).strip()
                field_comment = str(self._sheet.cell_value(FIELD_COMMENT_ROW, self._col)) #unicode
                #LOG_INFO("%s|%s|%s|%s", field_rule, field_type, field_name, field_comment)

                comment = str(field_comment.encode("utf-8"))

                self._LayoutComment(comment)

                self._LayoutOneField(field_rule, field_type, field_name)

                self._col += 1

        elif field_rule == "required_struct" or field_rule == "optional_struct":
            field_num = int(self._sheet.cell_value(FIELD_TYPE_ROW, self._col))
            struct_name = str(self._sheet.cell_value(FIELD_NAME_ROW, self._col)).strip()
            field_name = str(self._sheet.cell_value(FIELD_COMMENT_ROW, self._col)).strip()

            #LOG_INFO("%s|%d|%s|%s", field_rule, field_num, struct_name, field_name)


            if (self._IsStructDefined(struct_name)) :
                self._is_layout = False
            else :
                self._struct_name_list.append(struct_name)
                self._is_layout = True

            col_begin = self._col
            self._StructDefine(struct_name, field_num)
            col_end = self._col

            self._is_layout = True

            if repeated_num >= 1:
                field_rule = "repeated"
            elif field_rule == "required_struct":
                field_rule = "required"
            else:
                field_rule = "optional"

            self._LayoutOneField(field_rule, struct_name, field_name)

            actual_repeated_num = 1 if (repeated_num == 0) else repeated_num
            self._col += (actual_repeated_num-1) * (col_end-col_begin)
        else :
            self._col += 1
            return

    def _IsStructDefined(self, struct_name) :
        for name in self._struct_name_list :
            if name == struct_name :
                return True
        return False

    def _StructDefine(self, struct_name, field_num) :
        """嵌套结构定义"""

        self._col += 1
        self._LayoutStructHead(struct_name)
        self._IncreaseIndentation()
        self._field_index_list.append(1)

        while field_num > 0 :
            self._FieldDefine(0)
            field_num -= 1

        self._field_index_list.pop()
        self._DecreaseIndentation()
        self._LayoutStructTail()

    def _LayoutFileHeader(self) :
        """生成PB文件的描述信息"""
        self._output.append("/**\n")
        self._output.append("* @file:   " + self._pb_file_name + "\n")
        self._output.append("* @author: jameyli <jameyli AT tencent DOT com>\n")
        self._output.append("* @brief:  这个文件是通过工具自动生成的，建议不要手动修改\n")
        self._output.append("*/\n")
        self._output.append("\n")


    def _LayoutStructHead(self, struct_name) :
        """生成结构头"""
        if not self._is_layout :
            return
        self._output.append("\n")
        self._output.append(" "*self._indentation + "message " + struct_name + "{\n")

    def _LayoutStructTail(self) :
        """生成结构尾"""
        if not self._is_layout :
            return
        self._output.append(" "*self._indentation + "}\n")
        self._output.append("\n")

    def _LayoutComment(self, comment) :
        # 改用C风格的注释，防止会有分行
        if not self._is_layout :
            return
        if comment.count("\n") > 1 :
            if comment[-1] != '\n':
                comment = comment + "\n"
                comment = comment.replace("\n", "\n" + " " * (self._indentation + TAP_BLANK_NUM),
                        comment.count("\n")-1 )
                self._output.append(" "*self._indentation + "/** " + comment + " "*self._indentation + "*/\n")
        else :
            self._output.append(" "*self._indentation + "/** " + comment + " */\n")

    def _LayoutOneField(self, field_rule, field_type, field_name) :
        """输出一行定义"""
        if not self._is_layout :
            return
        if field_name.find('=') > 0 :
            name_and_value = field_name.split('=')
            self._output.append(" "*self._indentation + field_rule + " " + field_type \
                    + " " + str(name_and_value[0]).strip() + " = " + self._GetAndAddFieldIndex()\
                    + " [default = " + str(name_and_value[1]).strip() + "]" + ";\n")
            return

        if (field_rule != "required" and field_rule != "optional") :
            self._output.append(" "*self._indentation + field_rule + " " + field_type \
                    + " " + field_name + " = " + self._GetAndAddFieldIndex() + ";\n")
            return

        if field_type == "int32" or field_type == "int64"\
                or field_type == "uint32" or field_type == "uint64"\
                or field_type == "sint32" or field_type == "sint64"\
                or field_type == "fixed32" or field_type == "fixed64"\
                or field_type == "sfixed32" or field_type == "sfixed64" \
                or field_type == "double" or field_type == "float" :
                    self._output.append(" "*self._indentation + field_rule + " " + field_type \
                            + " " + field_name + " = " + self._GetAndAddFieldIndex()\
                            + " [default = 0]" + ";\n")
        elif field_type == "string" or field_type == "bytes" :
            self._output.append(" "*self._indentation + field_rule + " " + field_type \
                    + " " + field_name + " = " + self._GetAndAddFieldIndex()\
                    + " [default = \"\"]" + ";\n")
        else :
            self._output.append(" "*self._indentation + field_rule + " " + field_type \
                    + " " + field_name + " = " + self._GetAndAddFieldIndex() + ";\n")
        return

    def _IncreaseIndentation(self) :
        """增加缩进"""
        self._indentation += TAP_BLANK_NUM

    def _DecreaseIndentation(self) :
        """减少缩进"""
        self._indentation -= TAP_BLANK_NUM

    def _GetAndAddFieldIndex(self) :
        """获得字段的序号, 并将序号增加"""
        index = str(self._field_index_list[- 1])
        self._field_index_list[-1] += 1
        return index

    def _LayoutArray(self) :
        """输出数组定义"""
        self._output.append("message " + self._sheet_name + "_ARRAY {\n")
        self._output.append("    repeated " + self._sheet_name + " items = 1;\n}\n")

    def _Write2File(self) :
        """输出到文件"""
        pb_file = open(self.DIR_OUTPUT_PROTO+self._pb_file_name, "w+")
        pb_file.writelines(self._output)
        pb_file.close()


class DataParser:
    """解析excel的数据"""
    DIR_OUTPUT_TXT = ""
    DIR_OUTPUT_DATA = ""
    DIR_OUTPUT_PROTO = ""
    def __init__(self, xls_file_path, sheet_name,b_args, _workbook, _sheet):
        self._xls_file_path = xls_file_path
        self._sheet_name = sheet_name
        self.DIR_OUTPUT_TXT = b_args.otxtdir
        self.DIR_OUTPUT_DATA = b_args.odatadir
        self.DIR_OUTPUT_PROTO = b_args.oprotodir

        self._workbook = _workbook
        self._sheet = _sheet

        #try :
        #    self._workbook = xlrd.open_workbook(self._xls_file_path)
        #except (BaseException, e) :
        #    print ("open xls file(%s) failed!" %(self._xls_file_path))
        #    raise
#
        #try :
        #    self._sheet =self._workbook.sheet_by_name(self._sheet_name)
        #except( BaseException, e ):
        #    print ("open sheet(%s) failed!" %(self._sheet_name))
        #    raise

        self._row_count = len(self._sheet.col_values(0)) #行数
        self._col_count = len(self._sheet.row_values(0)) #列数

        self._row = 0
        self._col = 0

        try:
            self._module_name = FILE_PREFIX + self._sheet_name.lower() + "_pb2"
            print(self._module_name)
            sys.path.append(os.getcwd())
            sys.path.append(os.getcwd()+"\\ThirdParty")
            print(sys.path)
            modifyfile = os.getcwd()+'\\'+self._module_name+'.py'
            print(modifyfile)
            mfh = open(modifyfile,'r')
            mfhmls = mfh.readlines()
            tlen= len(mfhmls)
            mfh.close()
            for mfhline in range(0,tlen-1) :
                if('try:' in mfhmls[mfhline]):
                    mfhmls[mfhline] = "'''"+mfhmls[mfhline]
                if('    import ' in mfhmls[mfhline]):
                    mfhmls[mfhline] = "'''\n"+mfhmls[mfhline].replace('    ','')

            mfh=open(modifyfile,'w')
            mfh.writelines(mfhmls)
            mfh.close()
            
            exec('from '+self._module_name + ' import *');
            self._module = sys.modules[self._module_name]
        except BaseException as e :
            print ("load module(%s) failed" %(self._module_name))
            raise

    def Parse(self) :
        """对外的接口:解析数据"""
        #LOG_INFO("begin parse, row_count = %d, col_count = %d", self._row_count, self._col_count)

        item_array = getattr(self._module, self._sheet_name+'_ARRAY')()

        # 先找到定义ID的列(第一行从左到右不为空的第一列)
        id_col = 0
        for id_col in range(0, self._col_count) :
            info_id = str(self._sheet.cell_value(self._row, id_col)).strip()
            if info_id == "" :
                continue
            else :
                break

        #先把列名处理出来
        self.col_names = {}
        for id_col2 in range(id_col, self._col_count) :
            col_data_t = {}
            col_data_t["field_rule"] = str(self._sheet.cell_value(0, id_col2)).strip()

            if col_data_t["field_rule"] == "required" or col_data_t["field_rule"] == "optional" :
                col_data_t["field_name"] = str(self._sheet.cell_value(2, id_col2)).strip()
                if col_data_t["field_name"].find('=') > 0 :
                    col_data_t["name_and_value"] = col_data_t["field_name"].split('=')
                    col_data_t["field_name"] = str(col_data_t["name_and_value"][0]).strip()
                col_data_t["field_type"] = str(self._sheet.cell_value(1, id_col2)).strip()
            elif col_data_t["field_rule"] == "repeated" :
                # 若repeated第二行是类型定义，则表示当前字段是repeated，并且数据在单列用逗号相隔
                second_row = str(self._sheet.cell_value(FIELD_TYPE_ROW, id_col2)).strip()
                col_data_t["second_row"] = second_row
                if second_row.isdigit() or second_row.find(".") != -1 :
                    pass
                else :
                    col_data_t["field_type"] = second_row
                    col_data_t["field_name"] = str(self._sheet.cell_value(FIELD_NAME_ROW, id_col2)).strip()
            elif col_data_t["field_rule"] == "required_struct" or col_data_t["field_rule"] == "optional_struct":
                col_data_t["field_num"] = int(self._sheet.cell_value(FIELD_TYPE_ROW, id_col2))
                col_data_t["struct_name"] = str(self._sheet.cell_value(FIELD_NAME_ROW, id_col2)).strip()
                col_data_t["field_name"] = str(self._sheet.cell_value(FIELD_COMMENT_ROW, id_col2)).strip()

            self.col_names[id_col2] = col_data_t


        for self._row in range(4, self._row_count) :
            # 如果 id 是 空 直接跳过改行
            info_id = str(self._sheet.cell_value(self._row, id_col)).strip()
            if info_id == "" :
                LOG_WARN("%d is None", self._row)
                continue
            item = item_array.items.add()
            self._ParseLine(item)

        #LOG_INFO("parse result:\n%s", item_array)

        self._WriteReadableData2File(str(item_array))

        data = item_array.SerializeToString()
        if GEN_CHECK_MD5:

            md5file=open(self.DIR_OUTPUT_PROTO + FILE_PREFIX + self._sheet_name.lower() + ".proto",'rb')

            cur_md5=hashlib.md5(md5file.read()).hexdigest()

            md5file.close()

            print(cur_md5)

            self._WriteData2File(data,cur_md5,"r52422")
        else:
            self._WriteData2File(data)


        #comment this line for test .by kevin at 2013年1月12日 17:23:35
        LogHelp.close()

    def _ParseLine(self, item) :
        #LOG_INFO("%d", self._row)

        self._col = 0
        while self._col < self._col_count :
            self._ParseField(0, 0, item)

    def _ParseField(self, max_repeated_num, repeated_num, item) :
        field_rule = self.col_names[self._col]["field_rule"]

        if field_rule == "required" or field_rule == "optional" :
            field_name = self.col_names[self._col]["field_name"]
            field_type = self.col_names[self._col]["field_type"]

            #LOG_INFO("%d|%d", self._row, self._col)
            #LOG_INFO("%s|%s|%s", field_rule, field_type, field_name)

            if max_repeated_num == 0 :
                field_value = self._GetFieldValue(field_type, self._row, self._col)
                # 有value才设值
                if field_value != None :
                    item.__setattr__(field_name, field_value)
                self._col += 1
            else :
                if repeated_num == 0 :
                    if field_rule == "required" :
                        print ("required but repeated_num = 0")
                        raise
                else :
                    for col in range(self._col, self._col + repeated_num):
                        field_value = self._GetFieldValue(field_type, self._row, col)
                        # 有value才设值
                        if field_value != None :
                            item.__getattribute__(field_name).append(field_value)
                self._col += max_repeated_num

        elif field_rule == "repeated" :
            # 2011-11-29 修改
            # 若repeated第二行是类型定义，则表示当前字段是repeated，并且数据在单列用分好相隔
            second_row = self.col_names[self._col]["second_row"]
            #LOG_DEBUG("repeated|%s", second_row);

            if second_row.isdigit() or second_row.find(".") != -1 :
                # 这里后面一般会是一个结构体
                max_repeated_num = int(float(second_row))
                read = self._sheet.cell_value(self._row, self._col)
                repeated_num = 0 if read == "" else int(self._sheet.cell_value(self._row, self._col))

                #LOG_INFO("%s|%d|%d", field_rule, max_repeated_num, repeated_num)

                if max_repeated_num == 0 :
                    print ("max repeated num shouldn't be 0")
                    raise

                if repeated_num > max_repeated_num :
                    repeated_num = max_repeated_num

                self._col += 1
                self._ParseField(max_repeated_num, repeated_num, item)

            else :
                # 一般是简单的单字段，数值用分号相隔
                # 一般也只能是数字类型
                field_type = self.col_names[self._col]["field_type"]
                field_name = self.col_names[self._col]["field_name"]
                field_value_str = str(self._sheet.cell_value(self._row, self._col))
                #field_value_str = unicode(self._sheet.cell_value(self._row, self._col)).strip()

                # #LOG_INFO("%d|%d|%s|%s|%s",
                #         self._row, self._col, field_rule, field_type, field_name, field_value_str)

                #2013-01-24 jamey
                #增加长度判断
                if len(field_value_str) > 0:
                    #if field_value_str.find(";\n") > 0 :
                    #    field_value_list = field_value_str.split(";\n")
                    #else :
                    #    field_value_list = field_value_str.split(";")
                    field_value_list = json.loads(field_value_str)

                    for field_value in field_value_list :
                        if field_type == "bytes":
                            item.__getattribute__(field_name).append(field_value.encode("utf8"))
                        elif field_type == "string":
                            item.__getattribute__(field_name).append(str(field_value))
                        elif field_type == "float" or field_type == "double":
                            item.__getattribute__(field_name).append(float(field_value))
                        else:
                            item.__getattribute__(field_name).append(int(float(field_value)))

                self._col += 1

        elif field_rule == "required_struct" or field_rule == "optional_struct":
            field_num = self.col_names[self._col]["field_num"]
            struct_name = self.col_names[self._col]["struct_name"]
            field_name = self.col_names[self._col]["field_name"]

            #LOG_INFO("%s|%d|%s|%s", field_rule, field_num, struct_name, field_name)


            col_begin = self._col

            # 至少循环一次
            if max_repeated_num == 0 :
                struct_item = item.__getattribute__(field_name)
                self._ParseStruct(field_num, struct_item)

            else :
                if repeated_num == 0 :
                    if field_rule == "required_struct" :
                        print ("required but repeated_num = 0")
                        raise
                    # 先读取再删除掉
                    struct_item = item.__getattribute__(field_name).add()
                    self._ParseStruct(field_num, struct_item)
                    item.__getattribute__(field_name).__delitem__(-1)

                else :
                    for num in range(0, repeated_num):
                        struct_item = item.__getattribute__(field_name).add()
                        self._ParseStruct(field_num, struct_item)

            col_end = self._col

            max_repeated_num = 1 if (max_repeated_num == 0) else max_repeated_num
            actual_repeated_num = 1 if (repeated_num==0) else repeated_num
            self._col += (max_repeated_num - actual_repeated_num) * ((col_end-col_begin)/actual_repeated_num)

        else :
            self._col += 1
            return

    def _ParseStruct(self, field_num, struct_item) :
        """嵌套结构数据读取"""

        # 跳过结构体定义
        self._col += 1
        while field_num > 0 :
            self._ParseField(0, 0, struct_item)
            field_num -= 1

    def _GetFieldValue(self, field_type, row, col) :
        """将pb类型转换为python类型"""

        field_value = self._sheet.cell_value(row, col)
        #LOG_INFO("%d|%d|%s", row, col, field_value)

        try:
            if field_type == "int32" or field_type == "int64"\
                    or  field_type == "uint32" or field_type == "uint64"\
                    or field_type == "sint32" or field_type == "sint64"\
                    or field_type == "fixed32" or field_type == "fixed64"\
                    or field_type == "sfixed32" or field_type == "sfixed64" :
                        if len(str(field_value).strip()) <=0 :
                            return None
                        else :
                            return int(field_value)
            elif field_type == "double" or field_type == "float" :
                    if len(str(field_value).strip()) <=0 :
                        return None
                    else :
                        return float(field_value)
            elif field_type == "string" :
                field_value = str(field_value) #unicode
                if len(field_value) <= 0 :
                    return None
                else :
                    return field_value
            elif field_type == "bytes" :
                field_value = str(field_value).encode('utf-8') #unicode
                if len(field_value) <= 0 :
                    return None
                else :
                    return field_value
            else :
                return None
        except (BaseException, e) :
            print ("parse cell(%u, %u) error, please check it, maybe type is wrong." %(row, col))
            raise

    def _WriteData2File(self, data, md5, svn_ver) :
        file_name = self.DIR_OUTPUT_DATA + FILE_PREFIX + self._sheet_name.lower() + ".data"
        file = open(file_name, 'wb+')
        if GEN_CHECK_MD5:
            file.write((CHECK_MD5_HEAD+"\n"+md5+"\n"+svn_ver+"\n").encode())
        file.write(data)
        file.close()

    def _WriteReadableData2File(self, data) :
        file_name = self.DIR_OUTPUT_TXT + FILE_PREFIX + self._sheet_name.lower() + ".txt"
        file = open(file_name, 'w+')
        file.write(data)
        file.close()

def mainprocess(sheet_name,xls_file_path,b_args):
    
    if((not b_args.otype) or (b_args.otype == 'proto')):
        tool = SheetInterpreter(xls_file_path, sheet_name,b_args)
        
        tool.Interpreter()
        print ("Interpreter Success!!!")
    if((not b_args.otype) or (b_args.otype == 'data')):
        parser = DataParser(xls_file_path, sheet_name,b_args, tool._workbook, tool._sheet)
        try:
            parser.Parse()
        except Exception as e:
            dpee = DataParseErrorException()
            dpee.col = parser._col
            dpee.row = parser._row
            dpee.excelfilename = parser._xls_file_path
            dpee.sheetname = parser._sheet_name 
            dpee.exceptioninstance = e
            raise dpee
        print ("Parse Success!!!")




if __name__ == '__main__' :
    """入口"""
    b_args_parser = argparse.ArgumentParser(description='Convert EXCEL file to protobuf data')
    b_args_parser.add_argument('sheetname',help='Sheet name which need be converted')
    b_args_parser.add_argument('excelfilepath',help='Excel file path')
    b_args_parser.add_argument('-otype',choices=['proto','data'],help='output only proto or data,if not set ,output both')
    b_args_parser.add_argument('-odatadir',default="" ,help="data file output dir path ")
    b_args_parser.add_argument('-oprotodir',default="",help="proto file output dir path ")
    b_args_parser.add_argument('-otxtdir',default="",help="txt file contains data content output dir path ")
    b_args_parser.add_argument('-ocsharpdir',default="",help="csharp file contains define content output dir path ")
    
    b_args = b_args_parser.parse_args()
    print(b_args)
    sheet_name = b_args.sheetname
    xls_file_path = b_args.excelfilepath
    
    mainprocess(sheet_name,xls_file_path,b_args)
    

