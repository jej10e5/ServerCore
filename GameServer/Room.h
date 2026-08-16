#pragma once
#include "JobQueue.h"
class Room : public JobQueue
{
public:
	// 싱글스레드 환경인마냥 코딩
	void Enter(PlayerRef player);
	void Leave(PlayerRef player);
	void Broadcast(SendBufferRef sendBuffer);

public:
	map<int64, PlayerRef> _players;

};

extern shared_ptr<Room> GRoom;

