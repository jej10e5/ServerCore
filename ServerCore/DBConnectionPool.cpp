#include "pch.h"
#include "DBConnectionPool.h"

DBConnectionPool::DBConnectionPool()
{
}

DBConnectionPool::~DBConnectionPool()
{
	Clear();
}

bool DBConnectionPool::Connect(int32 connectionCount, const WCHAR* connectionString)
{
	WRITE_LOCK;

	if (::SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &_environment) != SQL_SUCCESS)
		return false;

	if (::SQLSetEnvAttr(_environment, SQL_ATTR_ODBC_VERSION, reinterpret_cast<SQLPOINTER>(SQL_OV_ODBC3), 0) != SQL_SUCCESS)
		return false;

	for (int32 i = 0;i < connectionCount;i++)
	{
		DBConnection* connection = xnew<DBConnection>();
		if (connection->Connect(_environment, connectionString) == false)
		{
			connection->Clear();
			xdelete(connection);
			return false;
		}

		_connections.push_back(connection);
	}

	return true;
}

void DBConnectionPool::Clear()
{
	WRITE_LOCK;

	// 커넥션을 모두 정리한 뒤에 environment를 해제해야 한다
	for (DBConnection* connection : _connections)
	{
		connection->Clear();
		xdelete(connection);
	}

	_connections.clear();

	if (_environment != SQL_NULL_HANDLE)
	{
		::SQLFreeHandle(SQL_HANDLE_ENV, _environment);
		_environment = SQL_NULL_HANDLE;
	}
}

DBConnection* DBConnectionPool::Pop()
{
	WRITE_LOCK;

	// 풀이 비었다는 건 Push를 빠뜨렸다는 뜻이므로 디버그 빌드에서 원인 지점을 바로 잡는다.
	// 다만 nullptr 반환 계약은 그대로 유지한다 (호출부가 고갈을 처리할 수 있도록).
	ASSERT_CRASH(_connections.empty() == false);

	if (_connections.empty())
		return nullptr;

	auto connection = _connections.back();
	_connections.pop_back();
	return connection;
}

void DBConnectionPool::Push(DBConnection* connection)
{
	WRITE_LOCK;
	_connections.push_back(connection);

}
