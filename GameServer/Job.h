#pragma once
class IJob
{
public:
	virtual void Excute() {}
};


class HealJob : public IJob
{
public: 
	virtual void Excute() override
	{
		// _targetÀ» Ã£¾Æ¼­
		// _target->AddHp(_healValue);
		cout << _target << "ÇÑÅ× Èú" << _healValue << "¸¸Å­ ÁÜ." << endl;
	}

public:
	uint64 _target = 0;
	uint64 _healValue = 0;
};

using JobRef = shared_ptr<IJob>;

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