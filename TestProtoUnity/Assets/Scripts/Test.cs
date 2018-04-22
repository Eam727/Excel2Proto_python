using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using ProtoBuf;
using System.IO;
using protos;

public class Test : MonoBehaviour
{

    void Start()
    {
        Activity_Reward data = Activity_RewardReader.GetInstance().GetInfo(3);
        Debug.LogError("data.name:" + data.order_number + ";data.appear_lv" + data.icon_empty);
    }

    private T ReadOneDataConfig<T>(string FileName)
    {
        FileStream fileStream;
        fileStream = GetDataFileStream(FileName);
        if (null != fileStream)
        {
            T t = Serializer.Deserialize<T>(fileStream);
            fileStream.Close();
            return t;
        }

        return default(T);
    }
    private FileStream GetDataFileStream(string fileName)
    {
        string filePath = GetDataConfigPath(fileName);
        if (File.Exists(filePath))
        {
            FileStream fileStream = new FileStream(filePath, FileMode.Open);
            return fileStream;
        }

        return null;
    }
    private string GetDataConfigPath(string fileName)
    {
        return Application.streamingAssetsPath + "/DataConfig/" + fileName + ".data";
    }
}


