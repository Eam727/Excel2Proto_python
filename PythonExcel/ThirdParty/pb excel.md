##**protobuf 导excel表格数据**

参考链接:[https://blog.csdn.net/linshuhe1/article/details/52062969](https://blog.csdn.net/linshuhe1/article/details/52062969 "https://blog.csdn.net/linshuhe1/article/details/52062969")

**一、protobuf简介：**

protobuf是由google公司发布的一个开源的项目，是一款方便而又通用的数据传输协议。所以我们在Unity中也可以借助protobuf来进行数据存储和网络协议两方面的开发，这里先说说数据存储部分的操作，也就是：

将.xls表格数据通过protobuf进行序列化，并在Unity中使用。


**1.需要资源下载**

Python3.5.2 安装方法：[python安装和配置](http://blog.csdn.net/linshuhe1/article/details/52056864)

protobuf-python-3.5.0安装方法：[protobuf-python-3.5.0.zip](https://github.com/google/protobuf/releases)
protoc-3.5.0-win32.zip

setuptools：这是Python的组件安装管理器，需要在安装protobuff组件前进行安装，到[setuptools](https://pypi.python.org/pypi/setuptools#downloads)官网下载插件的安装包，解压到指定目录，然后使用命令行进入安装包目录，执行指令：python setup.py install；

xlrd(xls reader)：这其实是读取xls表格数据的一个工具插件，到[xlrd官网](https://pypi.python.org/pypi/xlrd)下载xrld的安装包，解压安装包然后使用命令行进入安装包目录，执行指令：python setup.py install。


**2.流程图**

![](https://i.imgur.com/HvDdN0S.jpg)

 从上图可看出基本的操作步骤：


- xls表格文件，先通过xls_deploy_tool.py生成对应的.data文件和.proto文件，其中.data文件就是表格数据序列化后的结果，而.proto文件则是用于生成反序列化时使用的解析类的中间状态；
- 解析类.proto经过protoc.exe转换成.desc文件，用于后面通过protobuf-net等工具转化为特定的语言，这里我们需要得到的是C#解析类，即.cs类；
- 在Unity中导入protobuf-net.dll库，在C#代码中调用上述生成的.cs解析类来解析.data中的数据。

**二、导表环境配置：**

**1.Python相关配置：**

python安装时候可以放入自定义目录，勾选自动设置环境变量。这里需要注意，pb各个版本和python各个版本不是全部兼容，所以注意自己系统的环境变量里是否有多个版本python路径，确保系统里用兼容的python版本去执行pb代码。(这里使用的py3.5.2版本和pb3.5.0版本亲测兼容)



- **setuptools**：这是Python的组件安装管理器，需要在安装protobuf组件前进行安装，到[setuptools官网](https://pypi.python.org/pypi/setuptools#downloads)下载插件的安装包，解压到指定目录，然后使用命令行进入安装包目录，执行指令：`python setup.py install`；


- **Protobuf**：首先，我们将之前下载好的源码包protobuf-python-3.5.0.zip和编译包protoc-3.5.0-win32.zip压缩包解压到指定目录，路径最好不要包含中文；
- 这里我解压这些个文件都放在了F:\PythonExcel\ThirdParty文件夹下，我的批处理脚本和执行py脚本都放在了F:\PythonExcel文件夹下


- 然后复制protoc-3.5.0-win32.zip解压得到的protoc.exe到protobuf-3.5.0\src目录下；
在protobuf-3.5.0\python\google\protobuf下创建一个文件夹命名为compiler（安装完成后会在此目录下生成两个文件__init__.py和plugin_pb2.py）；
使用命令行进入到解压后的目录下面的Python目录，执行：`python setup.py install`；

- **xlrd(xls reader)**：这其实是读取xls表格数据的一个工具插件，到[xlrd官网](https://pypi.python.org/pypi/xlrd)下载xrld的安装包，解压安装包然后使用命令行进入安装包目录，执行指令：`python setup.py install`。

**2.导表外部工具：**

- xls_deploy_tool.py：这个工具其实是github上的一个开源的符合protobuff标准的根据excel自动生成匹配的PB的定义（.proto文件）并将数据序列化后生成二进制数据或者文本数据（.data文件）的一个工具，github下载地址：[xls_deploy_tool.py](https://github.com/jameyli/tnt/tree/master/python)，这里是2.x版本的，然后根据项目需求写了个3.x版本的，代码见附录。

- protoc.exe和protogen.exe：通过上面的工具，我们得到了两个文件：存储数据的.data文件和用于解析数据的.proto文件，但是我们在真正使用解析类来进行数据文件的解析时，必须是高级语言，当然protobuf-net提供很多种高级语言的支持。就像我们在Unity中我们使用的是C#语言，这需要两个工具来实现，一个是protobuf-2.5.0中的protoc.exe将.proto文件转换为“FileDescriptorSet”中间格式；另一个是使用protobuf-net中的protogen.exe，将中间格式的文件转换为最终状态，即高级语言的解析类.cs文件。

- 可以到github上下载protobuf-net的源码：[protobuf-net](https://github.com/linshuhe/protobuf-net)，下载后解压到本地，然后进入到解压后protobuf-net-master\protobuf-net目录下，通过Visual Studio打开protobuf-net.csproj：

- 选项选择：Net20,然后点击生成-生成protobuf-net(U)
- 编译完成后在当前目录下面的bin\Net20目录下，生成了编译后的文件，其中我们需要的是protobuf-net.dll
- 将protobuf-net.dll复制到protobuf-net-master\ProtoGen目录下，用Visual Studio打开ProtoGen.csproj，参照上面步骤编译ProtoGen项目，得到protobuf-net-master\ProtoGen\bin\Release目录下面的protogen.exe及一些额外的文件，但在真正使用时此目录下面的所有文件都是必须的：(若报错则刚才的dll也复制到报缺失的地方)
![](https://i.imgur.com/2OOUA4y.png)

![](https://i.imgur.com/WUpCInJ.png)

- 然后使用protogen把proto文件转为cs文件`call ThirdParty\protoGenTool\protogen -i:newprotoData\proto\mmo3d_activity_reward.proto -o:newprotoData\csharp\mmo3d_activity_reward.cs`

- 我这里使用封装了的加载data文件的接口，每个新的表导出都需要生成类实现接口：所以我们写了模版文件，然后每次读取一个sheet数据时候生成一段cs代码。这些都可以在bat文件中执行。

- 根据需要可以把生成的各种文件复制到某指定的目录。

**3.注意：**

(平台兼容问题)

由于直接把protobuf-net.dll放到项目中时，在iOS中会出现JIT错误（ExecutionEngineException: Attempting to JIT compile method）。原因是因为iOS不允许JIT（Just In Time），只允许AOT（Ahead Of Time）。

解决方法：
直接把protprotobuf-net-master\protobuf-net目录下面的全部源码复制到Unity项目的目录下面，但是由于protobuf-net的编译过程是unsafe编译，所以Unity会出现编译报错：
![](https://i.imgur.com/mIiDDoq.png)

需要在Assets目录下添加一个smsc.rsp文件，其内容很简单，只有一行“-unsafe”，添加完成后关闭Unity然后重新打开Unity，一切就正常了。


----------

附录：

    




























https://stackoverflow.com/questions/24512841/unity3d-unsafe-code-requires-the-unsafe-command-line-option-to-be-specified