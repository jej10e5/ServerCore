#pragma once
/* --------------
	RecvBuffer
--------------*/

// [wr][][][][][][][][][]
// [r][][][w][][][][][][] : 데이터를 받고 다음에 쓰는 커서 위치가 w
// [r][][][][][w][][][][]
// [][][][r][][w][][][][] : 패킷 완성 확인하면 읽어서 읽는 커서 위치가 바뀜
// 끝부분에서 끝나는게 아니라 처음 부분이랑 연결된 형태로 사용 -> 링버퍼 기법

// [][][][][][][][rw][][] : r/w 커서 위치가 운좋게 겹치면 커서 위치를 앞으로 변경 -> 복사 비용 없음!
// [rw][][][][][][][][][]

class RecvBuffer
{
	enum { BUFFER_COUNT = 10 };

public:
	RecvBuffer(int32 bufferSize);
	~RecvBuffer();

	void			Clean();
	bool			OnRead(int32 numOfBytes);
	bool			OnWrite(int32 numOfBytes);

	BYTE*			ReadPos() { return &_buffer[_readPos]; }
	BYTE*			WritePos() { return &_buffer[_writePos]; }
	int32			DataSize() { return _writePos - _readPos; }
	int32			FreeSize() { return _bufferSize - _writePos; }

private:
	int32			_capacity = 0;
	int32			_bufferSize = 0;
	int32			_readPos = 0;
	int32			_writePos = 0;
	Vector<BYTE>	_buffer;

};

