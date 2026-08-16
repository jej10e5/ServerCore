#pragma once
class JobQueue
{
public:
	JobRef Pop()
	{
		WRITE_LOCK;
		if (_jobs.empty())
			return nullptr;

		JobRef ret = _jobs.front();
		_jobs.pop();
		return ret;
	}

	void Push(JobRef job)
	{
		WRITE_LOCK;
		_jobs.push(job);
	}

private:
	USE_LOCK;
	queue<JobRef> _jobs;
};