#pragma once

#include "IocpCore.h"
#include "IocpEvent.h"
#include "NetAddress.h"

/*----------------------
	Session
----------------------*/
class Session : public IocpObject
{
	friend class Listener;
	friend class IocpCore;
	friend class Service;

public:
	Session();
	virtual ~Session();

public:
	/* 정보 관련 */
	void				SetNetAddress(NetAddress address) { _netAddress = address; }
	NetAddress			GetAddress() { return _netAddress; }
	SOCKET				GetSocket() { return _socket; }
	bool				IsConnected() { return _connected; }
	SessionRef			GetSessionRef() { return static_pointer_cast<Session>(shared_from_this()); }

private:
	/* 인터페이스 구현 */
	// IocpObject을(를) 통해 상속됨
	virtual HANDLE		GetHandle() override;
	virtual void		Dispatch(IocpEvent* iocpEvent, int32 numOfBytes = 0) override;

private:
	/* 전송 관련*/
	void				RegisterConnect();
	void				RegisterRecv();
	void				RegisterSend();

	void				ProcessConnect();
	void				ProcessRecv(int32 numOfBytes);
	void				ProcessSend(int32 numOfBytes);

	void				HandleError(int32 errCode);

public:
	// TEMP
	char _recvBuffer[1000];

private:
	SOCKET			_socket = INVALID_SOCKET;
	NetAddress		_netAddress = {};
	Atomic<bool>	_connected = false;

	
};

