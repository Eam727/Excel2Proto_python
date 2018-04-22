using System.Collections;
using System.Collections.Generic;
using protos;


public class Activity_TaskReader : BinaryDataReaderEx<Activity_Task, Activity_Task_ARRAY, Activity_TaskReader>
{
    public override string GetLoadFileName()
    {
        return "Config/data/mmo3d_activity_task.data";
    }

    protected override uint GetKey(Activity_Task info)
    {
        return info.id;
    }

    public override List<Activity_Task> GetDataList(Activity_Task_ARRAY dataArray)
    {
        return dataArray.items;
    }
    
    public override string GetProtoMd5()
    {
        return "d0fa83f1ac2f2aab4daa5b1ee44d9e5d";
    }
}


public class Activity_RewardReader : BinaryDataReaderEx<Activity_Reward, Activity_Reward_ARRAY, Activity_RewardReader>
{
    public override string GetLoadFileName()
    {
        return "Config/data/mmo3d_activity_reward.data";
    }

    protected override uint GetKey(Activity_Reward info)
    {
        return info.id;
    }

    public override List<Activity_Reward> GetDataList(Activity_Reward_ARRAY dataArray)
    {
        return dataArray.items;
    }
    
    public override string GetProtoMd5()
    {
        return "b9d00e4b2434a30775f762f202dd6dd3";
    }
}