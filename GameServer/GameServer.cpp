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

int main()
{
	WSAData wsaData;
	if (::WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
		return 0;

	SOCKET serverSocket = ::socket(AF_INET, SOCK_STREAM, 0);
	if (serverSocket == INVALID_SOCKET)
	{
		HandleError("Socket");
		return 0;
	}

	// 옵션을 해석하고 처리할 주체?
	// 소켓 코드 -> SOL_SOCKET
	// Ipv4 -> IPPROTO_IP
	// TCP 프로토콜 -> IPPROTO_TCP
	
	// SO_KEEPALIVE = 주기적으로 연결 상태 확인 여부 (TCP only)
	// 상대방이 소리소문없이 연결 끊는다면?
	// 주기적으로 TCP 프로토콜 연결 상태 확인 -> 끊어진 연결 감지
	bool enable = true;
	::setsockopt(serverSocket, SOL_SOCKET, SO_KEEPALIVE, (char*)&enable, sizeof(enable));

	// SO_LINGER = 지연하다
	// 송신 버퍼에 있는 데이터를 보낼 것인가? 날릴 것인가?
	// onoff = 0 이면 closesocket()이 바로 리턴, 아니면 linger초만큼 대기(default 0)
	// linger : 대기 시간
	LINGER linger;
	linger.l_onoff = 1;
	linger.l_linger = 5;
	::setsockopt(serverSocket, SOL_SOCKET, SO_LINGER, (char*)&linger, sizeof(linger));

	// Half-Close
	// SD_SEND : send 막는다
	// SD_RECEIVE : recv 막는다
	// SD_BOTH : 둘다 막는다
	::shutdown(serverSocket, SD_SEND);
	
	// 소켓 리소스 반환
	// send -> close socket
	::closesocket(serverSocket);

	// 윈속 종료
	::WSACleanup();
}