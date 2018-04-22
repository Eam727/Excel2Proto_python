using System;
using System.Collections.Generic;
using Net;
using UnityEngine;
using System.IO;

#pragma warning disable 0168 // variable declared but not used.
#pragma warning disable 0219 // variable assigned but not used.
#pragma warning disable 0414 // private field assigned but not used.
public interface IFileLoader
{
    string GetLoadFileName();
    void LoadDataFile(string datFileName);
}

public abstract class BinaryDataReaderEx<TData, TDataArray, TReader> : IFileLoader
    where TData : new()
    where TReader : IFileLoader, new()
{
    private Dictionary<uint, TData> data = null;

    private byte[] buffer = null;
    private static TReader g_instance = default(TReader);

    public static TReader GetInstance()
    {
        if (g_instance == null)
        {
            g_instance = new TReader();
            String fileName = g_instance.GetLoadFileName();
            try
            {
                g_instance.LoadDataFile(fileName);
            }
            catch (Exception e)
            {
                Debug.LogError(string.Format("read file : {0} failed, msg : {1}", fileName, e.Message));
            }
        }
        return g_instance;
    }

    public TData GetInfo(uint key)
    {
        TData info;
        if (this.data.TryGetValue(key, out info))
            return info;

        return default(TData);
    }

    public Dictionary<uint, TData> GetData()
    {
        return this.data;
    }
    public int GetCount()
    {
        return this.data.Count;
    }
    protected abstract uint GetKey(TData info);
    public abstract string GetLoadFileName();
    public virtual string GetProtoMd5() { return ""; }
    public abstract List<TData> GetDataList(TDataArray dataArray);

    public void ReloadData()
    {
        LoadDataFile(GetLoadFileName());
    }

    public void LoadDataFile(string FileName)
    {
        try
        {
            //首先检查用户数据目录里是否有该文件//
            //string file_name = CUtility.GetFullFilePath(FileName);
            string file_name = TempLoad.GetResFullPath(FileName);
            int item_size = 0;
            buffer = File.ReadAllBytes(file_name);
            int data_start = 0;
            if (buffer.Length > 38 && buffer[0] == 'M' && buffer[1] == 'p' && buffer[2] == 'd' && buffer[3] == '\n')
            {
                //取md5码
                int index = 4;
                while (buffer[index] != '\n' && index < 38) //MD5一般32位
                    index++;
                string md5 = System.Text.Encoding.Default.GetString(buffer, 4, index - 4);
                if (md5 != GetProtoMd5())
                {
                    Debug.LogError(string.Format("Load file({0}) failed, data md5 {1} != {2} (code md5), protobuf struct dismatch.", FileName, md5, GetProtoMd5()));
                }

                //取svn版本号
                data_start = index + 1;
                while (buffer.Length > data_start && buffer[data_start] != '\n' && data_start < 50)
                {
                    data_start++;
                }
                //Log.Debug("svn ver:{0}", System.Text.Encoding.Default.GetString(buffer, index+1, data_start - index - 1));

                data_start++;//跳过 \n 后面才是数据正文
                byte[] tbuf = buffer;
                buffer = new byte[tbuf.Length - data_start];
                Buffer.BlockCopy(tbuf, data_start, buffer, 0, tbuf.Length - data_start);
            }

            NetMsg message = new NetMsg(0, buffer);
            TDataArray datas = message.GetBody<TDataArray>();
            List<TData> dataList = GetDataList(datas);
            int count = dataList.Count;

            data = new Dictionary<uint, TData>(count);
            for (int i = 0; i < count; ++i)
            {
                try
                {
                    data.Add(GetKey(dataList[i]), dataList[i]);
                }
                catch (System.Exception e)
                {
                    Debug.LogError(string.Format("Load file({0}) data add key{1} failed, error({2})", FileName, GetKey(dataList[i]), e.ToString()));
                }
            }

            buffer = null;
        }
        catch (System.Exception e)
        {
            Debug.LogError(string.Format("Load file({0}) failed, error({1})", FileName, e.ToString()));
        }
    }
}

