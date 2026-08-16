#include "pch.h"
#include "JobQueue.h"
#include "GlobalQueue.h"

void JobQueue::Push(JobRef&& job)
{
	const int32 prevCount = _jobCount.fetch_add(1); // 전의 count 리턴
	_jobs.Push(job); //WRITE_LOCK

	// 첫번째 Job을 넣은 스레드가 실행까지 담당
	if (prevCount == 0)
	{
		// 이미 실행중인 JobQueue가 없으면 실행
		if (LCurrentJobQueue == nullptr)
		{
			Execute();
		}
		else
		{
			// 여유 있는 다른 스레드가 실행하도록 GlobalQueue에 넘긴다
			GGlobalQueue->Push(shared_from_this());
		}
	}
}

// 1) 일감이 너~무 몰리면?
// 2) DoAsync 타고 타고 가서~ 절대 끝나지 않는 상황 (일감이 한 스레드에 몰림)
void JobQueue::Execute()
{
	LCurrentJobQueue = this;
	while (true)
	{
		Vector<JobRef> jobs;
		_jobs.PopAll(OUT jobs);

		const int32 jobCount = static_cast<int32>(jobs.size());
		for (int32 i = 0;i < jobCount;i++)
			jobs[i]->Execute();

		// 남은 일감이 0개라면 종료
		if (_jobCount.fetch_sub(jobCount) == jobCount)
		{
			LCurrentJobQueue = nullptr;
			return;
		}

		const uint64 now = ::GetTickCount64();
		if (now >= LEndTickCount) 
		{// 내가 할당받은 시간보다 더 시간을 쓰는 경우
			LCurrentJobQueue = nullptr;

			// 여유 있는 다른 스레드가 실행하도록 GlobalQueue에 넘긴다
			GGlobalQueue->Push(shared_from_this());
			break;

		}
	}
}
