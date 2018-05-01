#pragma once
#include "frame_inc.h"
$includeheaderlines
#include <iostream>
#include <map>
using namespace std;

class ConstData
{
public:
	ConstData();
	~ConstData();
	bool Load(string path);

	/* data */
$mapdefinelines

$protoinstancelines
};

#define g_ConstData  CSingleton<ConstData>::GetInstance()