#include "pch.h"
#include <iostream>
#include "CorePch.h"
#include <atomic>
#include <mutex>
#include <windows.h>
#include <future>
#include "ThreadManager.h"

#include <WinSock2.h>
#include <mswsock.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

void HandleError(const char* cause)
{
	int32 errCode = ::WSAGetLastError();
	cout << cause << " ErrorCode : " << errCode << endl;
}

const int32 BUFSIZE = 1000;
struct Session
{
	WSAOVERLAPPED overlapped = {};
	SOCKET socket = INVALID_SOCKET;
	char recvBuffer[BUFSIZE] = {};
	int32 recvBytes = 0;
	int32 sendBytes = 0;

};

void CALLBACK RecvCallback(DWORD error, DWORD recvLen, LPWSAOVERLAPPED overlapped, DWORD flags)
{
	cout << "Data Recv Len Callback = " << recvLen << endl;

	// TODO : 에코 서버를 만든다면 WSASend()
	// 사실상 매개변수를 운영체제가 채워주고 여러 소켓 연결이 된다면 찾을수가 없음
	// 여기서 Session의 구조체에서 WSAOVERLAPPED 값을 첫번째 위치에 둔다면 
	// Session의 포인터와 overlapped의 포인터가 같아서
	// 넘겨받은 overlapped로 Session으로 형변환이 가능함
	Session* session = (Session*)overlapped;
}

int main()
{
	WSAData wsaData;
	if (::WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
		return 0;

	SOCKET listenSocket = ::socket(AF_INET, SOCK_STREAM, 0);
	if (listenSocket == INVALID_SOCKET)
		return 0;
	u_long on = 1;
	::ioctlsocket(listenSocket, FIONBIO, &on);

	SOCKADDR_IN serverAddr;
	::memset(&serverAddr, 0, sizeof(serverAddr));
	serverAddr.sin_family = AF_INET;
	serverAddr.sin_addr.s_addr = ::htonl(INADDR_ANY);
	serverAddr.sin_port = ::htons(7777);

	if (::bind(listenSocket, (SOCKADDR*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
		return 0;

	if (::listen(listenSocket, SOMAXCONN) == SOCKET_ERROR)
		return 0;

	cout << "Accept" << endl;

	//Overlapped 모델 (Completion Routine 콜백 기반)
	// - 비동기 입출력 함수 완료되면, 쓰레드마다 있는 APC 큐에 일감이 쌓임
	// - Alertable Wait 상태로 들어가서 APC 큐 비우기 (콜백 함수)
	// 단점) APC큐 스레드마다 있다. Alertable Wait 자체도 조금 부담
	// 단점) 이벤트 방식 소켓:이벤트 1:1 대응, 감시 자체도 64개밖에 지원 안함

	// IOCP (Completion Port) 모델
	// - APC -> Completion Port (스레드마다 있는건 아니고 1개. 중앙에서 관리하는 APC 큐?느낌)
	// - Alertable Wait -> CP 결과 처리를 GetQueuedCompletionStatus
	// 스레드랑 궁합이 굉장히 좋다.


	while (true)
	{
		SOCKADDR_IN clientAddr;
		int32 addrLen = sizeof(clientAddr);
		SOCKET clientSocket;

		while (true)
		{
			clientSocket = ::accept(listenSocket, (SOCKADDR*)&clientAddr, &addrLen);
			if (clientSocket != INVALID_SOCKET)
				break;

			if (::WSAGetLastError() == WSAEWOULDBLOCK)
				continue;

			// 문제 있는 상황
			return 0;
		}

		Session session = Session{ clientSocket };
		//WSAEVENT wsaEvent = ::WSACreateEvent();

		cout << "Client Connected!" << endl;

		while (true)
		{
			WSABUF wsaBuf;
			wsaBuf.buf = session.recvBuffer;
			wsaBuf.len = BUFSIZE;
			DWORD recvLen = 0;
			DWORD flags = 0;
			//::memset(&session.overlapped, 0, sizeof(session.overlapped));
			//session.overlapped.hEvent = wsaEvent;
			// recv 비동기 호출 - 운영체제가 RecvCallback 호출 (매개변수 알아서 채움)
			if (::WSARecv(clientSocket, &wsaBuf, 1, &recvLen, &flags, &session.overlapped, RecvCallback) == SOCKET_ERROR)
			{
				if (::WSAGetLastError() == WSA_IO_PENDING)
				{
					// Pending 데이터를 받지 못함 아직 문제는 아님
					// Alertable Wait

					::SleepEx(INFINITE, TRUE);
					//::WSAWaitForMultipleEvents(1, &wsaEvent, TRUE, WSA_INFINITE, TRUE);
					
				}
				else
				{
					// TODO : 문제 있는 상황
					break;
				}
			}
			else
			{
				cout << "Data Recv Len : " << recvLen << endl;
			}

		}

		::closesocket(session.socket);
		//::WSACloseEvent(wsaEvent);
	}

	// 윈속 종료
	::WSACleanup();
}
