
#include "ConstData.h"
#include <string>
#include <stdio.h>
#include <stdlib.h>
using namespace std;

#define PROTO_MD5_HEAD "Mpd\n"

ConstData::ConstData(){
}
ConstData::~ConstData(){
}

// auto release class
class outo_free_buf
{
public:
	outo_free_buf()
	:buffer(NULL)
	,bufSize(0)
	{

	}

	~outo_free_buf()
	{
		if(buffer != NULL)
		{
			free(buffer);
			buffer = NULL;
		}
	}

	bool buf_malloc(long size)
	{
		if(size <= 0)
			return false;

		bufSize = size;
		buffer = (char*) malloc(bufSize);
		if(NULL == buffer)
		{
			cout << "Out of memory! ConstData buffer can't create!" << endl;
			return false;
		}
		return true;
	}

	bool buf_realloc(long size)
	{
		char* bufold = buffer;
		buffer = (char*) realloc(buffer, sizeof(char)*size);
		if (buffer == NULL)
		{
			free(bufold);	//如果分配失败，则必须把原来的free掉！
			cout << "Out of memory! ConstData buffer can't realloc! new size:" << size << endl;
			return false;
		}

		bufSize = size;
		return true;
	}

	/* data */
	char* buffer;
	long bufSize;
};


$loadfunctionlines

bool ConstData::Load(string path)
{
	outo_free_buf buf;	//auto release buffer object

	if(!buf.buf_malloc(1*1024*1024))
	{
		LERROR("Out of memory! ConstData buffer can't create!");
		return false;
	}

$actloadfunctionlines

	return true;
}

