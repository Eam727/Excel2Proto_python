

public class ${pbname}Reader : BinaryDataReaderEx<${pbname}, ${pbname}_ARRAY, ${pbname}Reader>
{
    public override string GetLoadFileName()
    {
        return "Config/data/mmo3d_${pbnamelowercase}.data";
    }

    protected override uint GetKey(${pbname} info)
    {
        return info.id;
    }

    public override List<${pbname}> GetDataList(${pbname}_ARRAY dataArray)
    {
        return dataArray.items;
    }
    
    public override string GetProtoMd5()
    {
        return "${protomd5}";
    }
}