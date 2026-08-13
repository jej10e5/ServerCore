#include "pch.h"
#include "ServerPacketHandler.h"

PacketHandlerFunc GPacketHandler[UINT16_MAX];


// 직접 컨텐츠 작업자가 만들어야함.

bool Handle_INVALID(PacketSessionRef& session, BYTE* buffer, int32 len)
{
	return false;
}

bool Handle_S_TEST(PacketSessionRef& session, Protocol::S_TEST& pkt)
{
	return false;
}
