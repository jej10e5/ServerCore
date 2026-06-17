#include "pch.h"
#include <iostream>

#include <WinSock2.h>
#include <mswsock.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")

int main()
{
	int32 num = 0x12345678;
	// 윈속 초기화(ws2_32 라이브러리 초기화)
	// 관련 정보가 wsaData에 채워짐
	WSAData wsaData;
	if (::WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
		return 0;

	// 소켓 만들기
	// ad : Address FAmily (AF_INET = IPv4, AF_INET6 = IPv6)
	// type : TCP(SOCK_STREAM) vs UDP(SOCK_DGRAM)
	// protocol : 0
	// return : desciptor
	SOCKET clientSocket = ::socket(AF_INET, SOCK_STREAM, 0);
	if (clientSocket == INVALID_SOCKET)
	{
		int32 errCode = ::WSAGetLastError();
		cout << "Socket ErrorCode : " << errCode << endl;
		return 0;
	}

	// 연결할 목적지는 ? (IP주소 + Port) -> XX 아파트 YY 호
	SOCKADDR_IN serverAddr; //IPv4
	::memset(&serverAddr, 0, sizeof(serverAddr));
	serverAddr.sin_family = AF_INET;

	// serverAddr.sin_addr.s_addr = ::inet_addr("127.0.0.1"); // deprecated
	::inet_pton(AF_INET, "127.0.0.1", &serverAddr.sin_addr);

	// htons : host to network short - 호스트에서 네트워크 방식으로 변환한다
	// Little-Endian vs Big-Endian
	// ex) 0x12345678 4바이트 정수
	// low [0x78][0x56][0x34][0x12] high < little = intel cpu 같은거
	// low [0x12][0x34][0x56][0x78] hibh < big = network
	serverAddr.sin_port = ::htons(7777); // 연결할때 사용할 포트

	if (::connect(clientSocket, (SOCKADDR*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR)
	{
		int32 errCode = ::WSAGetLastError();
		cout << "Connect ErrorCode : " << errCode << endl;
		return 0;
	}

	// ----------------------------
	// 연결 성공! 이제부터 데이터 송수신 가능!

	cout << "Connected To Server";

	while (true)
	{
		//TODO
		this_thread::sleep_for(1s);
	}

	// ----------------------------

	// 소켓 리소스 반환
	::closesocket(clientSocket);

	// 윈속 종료
	::WSACleanup();
}