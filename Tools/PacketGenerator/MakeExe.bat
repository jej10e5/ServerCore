pushd %~dp0

pyinstaller --add-data "Templates;Templates" --onefile  PacketGenerator.py

MOVE .\dist\PacketGenerator.exe .\GenPackets.exe
@RD /S /Q .\build
@RD /S /Q .\dist
DEL /S /F /Q .\PacketGenerator.spec
PAUSE
