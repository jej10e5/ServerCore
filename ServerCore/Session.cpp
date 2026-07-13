#include "pch.h"
#include "Session.h"
#include "SocketUtils.h"
#include "Service.h"
/*----------------------
	Session
----------------------*/

Session::Session()
{
	_socket = SocketUtils::CreateSocket();
}

Session::~Session()
{
	SocketUtils::Close(_socket);
}

void Session::Disconnect(const WCHAR* cause)
{
	if (_connected.exchange(false) == false)
		return;

	// TEMP
	wcout << "Disconnect : "  << cause << endl;

	OnDisconnected(); // 컨텐츠 코드에서 오버로딩
	SocketUtils::Close(_socket);
	GetService()->ReleaseSession(GetSessionRef());
}

HANDLE Session::GetHandle()
{
	return reinterpret_cast<HANDLE>(_socket);
}

void Session::Dispatch(IocpEvent* iocpEvent, int32 numOfBytes)
{
	switch(iocpEvent->eventType)
	{
		case EventType::Connect:
			ProcessConnect();
			break;
		case EventType::Recv:
			ProcessRecv(numOfBytes);
			break;
		case EventType::Send:
			ProcessSend(numOfBytes);
			break;

	}
}

void Session::RegisterConnect()
{
}

void Session::RegisterRecv()
{
	if (IsConnected() == false)
		return;

	// 실시간으로 만들어도 좋지만 세션에 멤버 변수로 들고 있으면
	// 재사용 측면에서도 좋음. 근데 구현 자체는 둘 다 상관 없다.
	// RecvEvent* recvEvent = xnew<RecvEvent>();
	// recvEvent->owner = shared_from_this();
	_recvEvent.Init();
	_recvEvent.owner = shared_from_this(); // Add_REF
	// WSARecv 걸어 주기 전에 REF 증가 시키기

	WSABUF wsabuf;
	wsabuf.buf = reinterpret_cast<char*>(_recvBuffer);
	wsabuf.len = len32(_recvBuffer);
	
	DWORD numOfBytes = 0;
	DWORD flags = 0;
	if (SOCKET_ERROR == ::WSARecv(_socket, &wsabuf, 1, OUT &numOfBytes, OUT &flags, &_recvEvent, nullptr))
	{
		int32 errorCode = ::WSAGetLastError();
		if (errorCode != WSA_IO_PENDING)
		{
			HandleError(errorCode);
			_recvEvent.owner = nullptr; // Release_REF
		}
	}

}

void Session::RegisterSend()
{
}

void Session::ProcessConnect()
{
	_connected.store(true);

	// 세션 등록
	GetService()->AddSession(GetSessionRef());

	// 컨텐츠 코드에서 오버로딩
	OnConnected();

	// 수신 등록
	RegisterRecv();
}

void Session::ProcessRecv(int32 numOfBytes)
{
	_recvEvent.owner = nullptr; // Release_REF
	if (numOfBytes == 0)
	{
		Disconnect(L"Recv 0");
		return;
	}

	// TODO
	cout << "Recv Data Len = " << numOfBytes << endl;

	// 수신 등록
	RegisterRecv();

}

void Session::ProcessSend(int32 numOfBytes)
{
}

void Session::HandleError(int32 errorCode)
{
	switch (errorCode)
	{
	case WSAECONNRESET:
	case WSAECONNABORTED:
		Disconnect(L"HandleError");
		break;
	default:
		// TODO : Log
		cout << "Handle Error : " << errorCode << endl;
		break;
	}
}
