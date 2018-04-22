using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using ProtoBuf;

namespace Net
{
    /// <summary>
    /// 
    /// </summary>
    public partial class NetMsg
    {
        public const int BODY_SIZE_SIZE = 4;
        public const int MSG_TYPE_SIZE = 2;
        public const int TAG_SIZE = 2;
        public const ushort TAG = 138;
        public const int SEQ_NO_SIZE = 2;
        public const int HEAD_SIZE = BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE + SEQ_NO_SIZE;
        private int mSize = 0;
        private ushort mType = 0;
        public byte[] data = null;
        public bool isRetry = false;
        public long recvtime = 0;
        public NetMsg()
        {
            //
        }

        public NetMsg(ushort msgType, byte[] body)
        {
            data = new byte[body.Length + BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE + SEQ_NO_SIZE];
            SetBodySizeBuff(body.Length);
            SetMsgTypeBuff(msgType);
            SetTagBuff();
            SetProtoBody(body);
        }

        public NetMsg Clone()
        {
            NetMsg newMsg = new NetMsg();
            newMsg.mSize = mSize;
            if (data != null)
            {
                newMsg.data = new byte[data.Length];
                Array.Copy(data, newMsg.data, data.Length);
            }
            return newMsg;
        }

        public void Reset()
        {
            mType = 0;
            mSize = 0;
            data = null;
        }

        private void SetBodySizeBuff(int size)
        {
            byte[] tmp = BitConverter.GetBytes(size);
            Array.Copy(tmp, 0, data, 0, BODY_SIZE_SIZE);
        }

        private void SetMsgTypeBuff(ushort msgType)
        {
            byte[] tmp = BitConverter.GetBytes(msgType);
            Array.Copy(tmp, 0, data, BODY_SIZE_SIZE, MSG_TYPE_SIZE);
        }

        private void SetTagBuff()
        {
            byte[] tmp = BitConverter.GetBytes(TAG);
            Array.Copy(tmp, 0, data, BODY_SIZE_SIZE + MSG_TYPE_SIZE, TAG_SIZE);
        }

        public void SetSeqNoBuff(ushort seqNo)
        {
            byte[] tmp = BitConverter.GetBytes(seqNo);
            Array.Copy(tmp, 0, data, BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE, SEQ_NO_SIZE);
        }

        private void SetProtoBody(byte[] body)
        {
            Array.Copy(body, 0, data, BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE + SEQ_NO_SIZE, body.Length);
        }

        public bool IsComplete()
        {
            return (GetProtocolSize() + BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE + SEQ_NO_SIZE) == mSize;
        }

        public int GetProtocolSize()
        {
            if (data == null || data.Length < BODY_SIZE_SIZE)
            {
                return -1;
            }
            else
            {
                return BitConverter.ToInt32(data, 0);
            }
        }

        public ushort MsgType
        {
            get
            {
                if (mType > 0)
                {
                    return mType;
                }
                else
                {
                    if (data == null || data.Length < BODY_SIZE_SIZE + MSG_TYPE_SIZE)
                    {
                        return 0;
                    }
                    else
                    {
                        mType = BitConverter.ToUInt16(data, BODY_SIZE_SIZE);
                        return mType;
                    }
                }
            }

        }

        public ushort GetSeqNo()
        {
            if (data == null || data.Length < BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE + SEQ_NO_SIZE)
            {
                return 0;
            }
            else
            {
                return BitConverter.ToUInt16(data, BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE);
            }
        }

        public T GetBody<T>()
        {
            MemoryStream stream = new MemoryStream(data, BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE + SEQ_NO_SIZE, data.Length - (BODY_SIZE_SIZE + MSG_TYPE_SIZE + TAG_SIZE + SEQ_NO_SIZE));
            T rep = ProtoBuf.Serializer.Deserialize<T>(stream);
            return rep;
        }
    }
}