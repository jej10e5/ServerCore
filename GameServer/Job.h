#pragma once

// C++11 apply
template<int... Remains>
struct seq
{};

template<int N, int... Remains>
struct gen_seq : gen_seq<N-1, N-1, Remains...>
{};

template<int... Remains>
struct gen_seq<0, Remains...> : seq<Remains...>
{};

template<typename Ret, typename... Args>
void xapply(Ret(*func)(Args...), std::tuple<Args...>& tup)
{
	return xapply_helper(func, gen_seq<sizeof...(Args)>(), tup);
}

template<typename F, typename... Args, int... ls>
void xapply_helper(F func, seq<ls...>, std::tuple<Args...>& tup)
{
	// 모든 튜블의 인자를 다 넘겨줌
	(func)(std::get<ls>(tup)...);
}

template<typename T, typename Ret, typename... Args>
void xapply(T* obj, Ret(T::*func)(Args...), std::tuple<Args...>& tup)
{
	return xapply_helper(obj, func, gen_seq<sizeof...(Args)>(), tup);
}

template<typename T, typename F, typename... Args, int... ls>
void xapply_helper(T* obj, F func, seq<ls...>, std::tuple<Args...>& tup)
{
	// 모든 튜블의 인자를 다 넘겨줌
	(obj->*func)(std::get<ls>(tup)...);
}


// 함수자 (Functor)
class IJob
{
public:
	virtual void Execute() {}
};

template<typename Ret, typename... Args>
class FuncJob : public IJob
{
	using FuncType = Ret(*)(Args...);
public:
	FuncJob(FuncType func, Args... args) : _func(func), _tuple(args...)
	{

	}

	virtual void Execute() override
	{
		//std::apply(_func, _tuple); // C++17
		xapply(_func, _tuple);
	}

private:
	FuncType _func;
	std::tuple<Args...> _tuple;
};

template<typename T, typename Ret, typename... Args>
class MemberJob : public IJob
{
	using FuncType = Ret(T::*)(Args...);
public:
	MemberJob(T* obj, FuncType func, Args... args) : _obj(obj),_func(func), _tuple(args...)
	{

	}

	virtual void Execute() override
	{
		//std::apply(_func, _tuple); // C++17
		xapply(_obj, _func, _tuple);
	}

private:
	T*					_obj;
	FuncType			_func;
	std::tuple<Args...> _tuple;
};



//========================================



class HealJob : public IJob
{
public: 
	virtual void Execute() override
	{
		// _target을 찾아서
		// _target->AddHp(_healValue);
		cout << _target << "한테 힐" << _healValue << "만큼 줌." << endl;
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