using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;

public class TempLoad : MonoBehaviour {

    public static string bundleResPath = "/BundleResources";
    public static string[] ResourcesPath =
{
        Application.persistentDataPath + bundleResPath,         //热跟资源路径
        Application.streamingAssetsPath + bundleResPath         //随包资源路径
    };

    public static string GetResFullPath(string fileName)
    {
        string path = null;
        fileName = fileName.ToLower();

        if (!fileName.StartsWith("/"))
            fileName = "/" + fileName;

        if (false)
        {
            path = Application.dataPath + fileName;
            path = path.Replace("\\", @"/");
        }
        else
        {
            for (int i = 0; i < ResourcesPath.Length; i++)
            {
                path = ResourcesPath[i] + fileName;
                path = path.Replace("\\", @"/");
                //path = "file://"+path;
                if (File.Exists(path))
                    break;
            }
        }
        return path;
    }
}