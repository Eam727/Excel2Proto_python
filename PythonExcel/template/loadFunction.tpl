static bool load_${pbname}(string& path, outo_free_buf& buf)
{
    string fileName = "";
    FILE * pFile = NULL;
    long lSize = 0;
    size_t result = 0;

    fileName = path+"/mmo3d_${pbnamelowercase}.data";
    pFile = fopen(fileName.c_str(), "rb");
    if (pFile==NULL)
    {
        LERROR("ConstData::Load open file fail: " << fileName);
        return false;
    }

    fseek(pFile , 0 , SEEK_END);
    lSize = ftell(pFile);
    rewind (pFile);

    if(lSize > buf.bufSize) 
    {
        if(!buf.buf_realloc(lSize))
        {
            LERROR("ConstData::Load new size:" << lSize << " out of memory! file:" << fileName);
            fclose(pFile);
            return false;
        }
    }

    result = fread(buf.buffer,1,lSize,pFile);
    if ((long)result != lSize)
    {
        LERROR("ConstData::Load read file fail: " << fileName << " size:" << result);
        fclose(pFile);
        return false;
    }
    fclose (pFile);
    //check md5
    int32_t index = 0;
    if(strncmp(buf.buffer,PROTO_MD5_HEAD,4) == 0)
    {
        if(strncmp(buf.buffer + 4,"${protomd5}",32) != 0)
        {
            string md5(buf.buffer,4,32);
            LERROR("ConstData::Load read file fail: " << fileName << " md5 diff data:" << md5 << ", code:${protomd5}, May different protobuf struct!");
            return false;
        }
        index = 38;
        while(index < lSize && buf.buffer[index++] != '\n' && index < 50) //skip to svn_ver\n
            continue;
    }

    g_ConstData.pb_${pbname}.Clear();
    g_ConstData.m_${pbname}.clear();
    if(!g_ConstData.pb_${pbname}.ParseFromArray(buf.buffer+index,lSize-index))
    {
        
        LWARN("ConstData::Load ParseFromArray failed! file:" << fileName);
        return false;
    }

    for(int i=0;i < g_ConstData.pb_${pbname}.items_size(); ++i)
    {
        g_ConstData.m_${pbname}[g_ConstData.pb_${pbname}.items(i).id()] = &g_ConstData.pb_${pbname}.items(i);
    }

    return true;
}