#pragma once
#include "Job.h"
class Room
{
public:
	// 싱글스레드 환경인마냥 코딩
	void Enter(PlayerRef player);
	void Leave(PlayerRef player);
	void Broadcast(SendBufferRef sendBuffer);

public:
	// 멀티스레드 환경에서는 일감으로 접근
	void PushJob(JobRef job) { _jobs.Push(job); }
	void FlushJob();

	template<typename T, typename Ret, typename... Args>
	void PushJob(Ret(T::* memFunc)(Args...), Args... args)
	{
		auto job = MakeShared<MemberJob<T, Ret, Args...>>(static_cast<T*>(this), memFunc, args...);
		_jobs.Push(job);

	}


public:
	map<int64, PlayerRef> _players;
	JobQueue _jobs;
};

extern Room GRoom;

