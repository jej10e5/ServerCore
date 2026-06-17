# ServerCore

Windows C++ 기반 게임 서버 코어 프로젝트입니다. 현재 저장소는 서버 코어 정적 라이브러리와 이를 사용하는 서버/클라이언트 실행 프로젝트로 구성되어 있으며, 메모리 관리, 스레드/락 관리, 데드락 감지, 기본 TCP 접속 흐름을 단계적으로 구현하고 있습니다.

## 프로젝트 구성

| 프로젝트 | 형식 | 역할 |
| --- | --- | --- |
| `ServerCore` | Static Library | 공용 타입, 메모리 풀, STL allocator, 스레드 매니저, RW SpinLock, 데드락 프로파일러 등 서버 코어 기능 |
| `GameServer` | Application | `ServerCore`를 사용하는 서버 실행 프로젝트. 현재 WinSock TCP 서버로 `7777` 포트를 열고 클라이언트 접속을 수락 |
| `DummyClient` | Application | 로컬 서버(`127.0.0.1:7777`)에 접속하는 테스트 클라이언트 |

솔루션 파일은 `Server.sln`입니다.

## 주요 기능

### 메모리 관리

- `Memory`, `MemoryPool`, `Allocator` 기반의 커스텀 할당 경로
- 작은 크기 할당을 크기별 풀로 분산해 재사용
- `xnew`, `xdelete`, `MakeShared` 헬퍼 제공
- `StlAllocator`를 통해 STL 컨테이너와 커스텀 allocator 연동

### 스레드와 락

- `ThreadManager`를 통한 스레드 생성/조인 및 TLS 초기화
- `Lock` 기반 RW SpinLock
- `ReadLockGuard`, `WriteLockGuard` RAII 락 가드
- `DeadLockProfiler`를 통한 락 획득 순서 기록 및 사이클 검사

### 네트워크 접속 흐름

- `GameServer`에서 WinSock 초기화 후 TCP listen socket 생성
- `INADDR_ANY:7777`에 bind/listen
- `DummyClient`에서 `127.0.0.1:7777`로 connect
- 서버에서 `accept` 후 클라이언트 IP 출력

현재 네트워크 코드는 연결 성립 확인 단계이며, 패킷 송수신, 세션 관리, 비동기 I/O는 아직 구현 전입니다.

## 개발 환경

- Windows
- Visual Studio 2019 이상 권장
- C++ 프로젝트
- WinSock2 사용 (`ws2_32.lib`)

## 빌드 방법

1. Visual Studio에서 `Server.sln`을 엽니다.
2. 구성은 `Debug|x64` 또는 `Release|x64`를 선택합니다.
3. 솔루션 빌드를 실행합니다.

빌드 결과물 위치:

- 실행 파일: `Binary/<Configuration>/`
- 정적 라이브러리: `Libraries/<Configuration>/`

예시:

```text
Binary/Debug/GameServer.exe
Binary/Debug/DummyClient.exe
Libraries/Debug/ServerCore.lib
```

## 실행 방법

1. `GameServer`를 먼저 실행합니다.
2. 서버가 `7777` 포트에서 대기하는 상태가 되면 `DummyClient`를 실행합니다.
3. 접속이 성공하면 서버 콘솔에 클라이언트 IP가 출력됩니다.

예상 흐름:

```text
GameServer: Client Connected! IP = 127.0.0.1
DummyClient: Connected To Server
```

주의할 점:

- 현재 서버와 클라이언트 모두 무한 루프로 유지됩니다.
- 정상 종료 시 소켓 정리 경로가 아직 충분히 정리되어 있지 않습니다.
- `7777` 포트가 이미 사용 중이면 서버의 `bind`가 실패할 수 있습니다.

## 디렉터리 구조

```text
.
├── Server.sln
├── ServerCore/
│   ├── Memory.*              # 메모리 관리자
│   ├── MemoryPool.*          # 크기별 메모리 풀
│   ├── Allocator.*           # Base/Pool/Stomp/STL allocator
│   ├── ThreadManager.*       # 스레드 실행 관리
│   ├── Lock.*                # RW SpinLock 및 RAII guard
│   ├── DeadLockProfiler.*    # 락 순서 추적 및 데드락 검사
│   ├── CoreGlobal.*          # 전역 코어 객체
│   ├── CoreTLS.*             # TLS 데이터
│   └── TypeCast.h            # 타입 캐스팅 유틸리티
├── GameServer/
│   └── GameServer.cpp        # TCP 서버 실행 진입점
├── DummyClient/
│   └── DummyClient.cpp       # TCP 클라이언트 실행 진입점
├── Binary/                   # 실행 파일 출력 경로
├── Libraries/                # 정적 라이브러리 출력 경로
└── document/
    ├── architecture/         # 아키텍처 문서
    └── changes/              # 변경점 분석 리포트
```


## 현재 구현 범위와 다음 단계

현재 구현된 범위:

- 서버 코어 라이브러리의 기본 메모리/스레드/락 인프라
- 서버/클라이언트 간 로컬 TCP 접속 확인
- 아키텍처 및 변경점 HTML 문서화

다음 단계 후보:

- 접속된 클라이언트 소켓의 생명주기 관리
- send/recv 기반 패킷 송수신
- 세션 객체 도입
- IOCP 또는 비동기 네트워크 모델 적용
- 서버 종료 시 리소스 정리 경로 보강
