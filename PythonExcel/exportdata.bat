@echo off
rem Parse Excel to Proto and data

del  /F /S /Q .\newprotoData
mkdir .\newprotoData\data
mkdir .\newprotoData\proto
mkdir .\newprotoData\pbc
mkdir .\newprotoData\txt
mkdir .\newprotoData\csharp
mkdir .\newprotoData\cpp

rem xcopy ..\protobuftools\protolist.txt protolist.txt /y

rem STEP1 gen proto and data
D:Python3.5.2\python.exe dealNewXls.py -odatadir .\newprotoData\data\ -oprotodir .\newprotoData\proto\ -otxtdir .\newprotoData\txt\ -ocsharpdir .\newprotoData\csharp\\

rem STEP2 gen pbc
cd .\newprotoData\proto\

setlocal enabledelayedexpansion
for /r %%i in (*.proto) do ( 
	set pbname=%%~nxi
	set pbname=!pbname:~0,-5!pbc	
	..\..\protoc --descriptor_set_out ..\pbc\!pbname! %%~nxi
)

cd ..\..\
call ThirdParty\protoGenTool\protogen -i:newprotoData\proto\mmo3d_activity_reward.proto -o:newprotoData\csharp\mmo3d_activity_reward.cs
call ThirdParty\protoGenTool\protogen -i:newprotoData\proto\mmo3d_activity_task.proto -o:newprotoData\csharp\mmo3d_activity_task.cs

rem STEP3 gen constdata.* TableDataReader.cs
rem ..\EamPB\python.exe gencpploader.py ..\newprotoData\protolist.txt ..\newprotoData\newprotoData\cpp

D:Python3.5.2\python.exe gencsharploader.py .\protolist.txt .\newprotoData\csharp .\newprotoData\proto\


pause
rem STEP4 copy allfile to  client or server dir
cd ..\newdataexport

copy .\newprotoData\data\*.data C:\work\mmo3d_client\trunk\mmo3d\Assets\Config\data\ /y
copy .\newprotoData\data\*.data D:\serverwork\S8\mmo3d\server\trunk\classes\release\data /y

copy .\newprotoData\pbc\*.pbc C:\work\mmo3d_client\trunk\mmo3d\Assets\Config\pbc\ /y
copy .\newprotoData\csharp\*.cs C:\work\mmo3d_client\trunk\mmo3d\Assets\Code\pbcsharpgen\ /y

pause