#pragma once
#include "Job.h"
class Room
{
	friend class EnterJob;
	friend class LeaveJob;
	friend class BroadecastJob;
private:
	// 싱글스레드 환경인 마냥 코딩
	void Enter(PlayerRef player);
	void Leave(PlayerRef player);
	void Broadcast(SendBufferRef sendBuffer);

public:
	// 멀티스레드 환경에서는 일감으로 접근
	void PushJob(JobRef job) { _jobs.Push(job); }
	void FlushJob();

public:
	map<int64, PlayerRef> _players;
	JobQueue _jobs;
};

extern Room GRoom;

// Room Jobs
class EnterJob : public IJob
{
public:
	EnterJob(Room& room, PlayerRef player) : _room(room), _player(player)
	{

	}

	virtual void Excute() override
	{
		_room.Enter(_player);
	}

public:
	Room& _room;
	PlayerRef _player;
};

class LeaveJob : public IJob
{
public:
	LeaveJob(Room& room, PlayerRef player) : _room(room), _player(player)
	{

	}

	virtual void Excute() override
	{
		_room.Leave(_player);
	}

public:
	Room& _room;
	PlayerRef _player;
};

class BroadecastJob : public IJob
{
public:
	BroadecastJob(Room& room, SendBufferRef sendBuffer) : _room(room), _sendBuffer(sendBuffer)
	{

	}

	virtual void Excute() override
	{
		_room.Broadcast(_sendBuffer);
	}

public:
	Room& _room;
	SendBufferRef _sendBuffer;
};