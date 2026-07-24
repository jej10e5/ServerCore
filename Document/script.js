(function () {
  const topics = [
    { file: "winsock-basic-connection.html", title: "Winsock 기본 연결" },
    { file: "blocking-echo-server.html", title: "블로킹 에코 서버" },
    { file: "tcp-byte-stream.html", title: "TCP 바이트 스트림" },
    { file: "socket-options.html", title: "소켓 옵션과 종료" },
    { file: "nonblocking-socket.html", title: "논블로킹 소켓" },
    { file: "event-multiplexing.html", title: "이벤트 기반 다중화" },
    { file: "overlapped-io.html", title: "Overlapped I/O" },
    { file: "iocp-overview.html", title: "IOCP Accept 흐름 Overview" },
    { file: "iocp-owner-dispatch.html", title: "IOCP owner 기반 Dispatch" },
    { file: "SendBuffer_Git_Comparison_Report.html", title: "SendBuffer Git 비교 보고서" },
    { file: "packet-session-git-comparison.html", title: "PacketSession 로컬 변경 분석" }
  ];

  const keywords = new Set([
    "alignas", "alignof", "auto", "bool", "break", "case", "catch", "char", "class", "const",
    "constexpr", "continue", "decltype", "default", "delete", "do", "double", "else", "enum",
    "explicit", "extern", "false", "float", "for", "friend", "if", "inline", "int", "long",
    "namespace", "new", "nullptr", "operator", "private", "protected", "public", "return",
    "short", "signed", "sizeof", "static", "struct", "switch", "template", "this", "throw",
    "true", "try", "typedef", "typename", "union", "unsigned", "using", "virtual", "void",
    "volatile", "while"
  ]);

  const types = new Set([
    "DWORD", "FD_SET", "LINGER", "LPWSAOVERLAPPED", "SOCKADDR", "SOCKADDR_IN", "SOCKET",
    "WSABUF", "WSADATA", "WSAData", "WSAEVENT", "WSANETWORKEVENTS", "WSAOVERLAPPED",
    "int32", "uint32", "u_long", "vector", "IocpCore", "IocpEvent", "IocpObjectRef",
    "Session", "SessionRef", "PacketSession", "PacketSessionRef", "PacketHeader",
    "SendBufferRef", "AcceptEvent", "RecvEvent", "ULONG_PTR"
  ]);

  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function span(className, value) {
    return `<span class="${className}">${escapeHtml(value)}</span>`;
  }

  function classify(token, nextToken) {
    if (token.startsWith("//") || token.startsWith("/*")) {
      return span("tok-comment", token);
    }

    if (token.startsWith('"') || token.startsWith("'")) {
      return span("tok-string", token);
    }

    if (/^#\s*\w+/.test(token)) {
      return span("tok-macro", token);
    }

    if (/^\d/.test(token)) {
      return span("tok-number", token);
    }

    if (keywords.has(token)) {
      return span("tok-keyword", token);
    }

    if (types.has(token) || /^[A-Z_][A-Z0-9_]{2,}$/.test(token)) {
      return span("tok-type", token);
    }

    if (/^[A-Za-z_]\w*$/.test(token) && nextToken === "(") {
      return span("tok-function", token);
    }

    if (token === "::" || token === "->" || token === "." || token === "&" || token === "*") {
      return span("tok-operator", token);
    }

    return escapeHtml(token);
  }

  function highlightCpp(source) {
    const pattern = /\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#\s*\w+|\b[A-Za-z_]\w*\b|\b\d+(?:\.\d+)?\b|::|->|[(){}[\].,&*+\-/=<>!|?:;%]/g;
    let output = "";
    let cursor = 0;
    let match;

    while ((match = pattern.exec(source)) !== null) {
      const token = match[0];
      output += escapeHtml(source.slice(cursor, match.index));
      const nextToken = source.slice(pattern.lastIndex).match(/\S/);
      output += classify(token, nextToken ? nextToken[0] : "");
      cursor = pattern.lastIndex;
    }

    output += escapeHtml(source.slice(cursor));
    return output;
  }

  document.querySelectorAll("pre code.language-cpp").forEach((code) => {
    code.innerHTML = highlightCpp(code.textContent);
  });

  const current = location.pathname.split(/[\\/]/).pop();
  const currentIndex = topics.findIndex((topic) => topic.file === current);
  if (currentIndex === -1) {
    return;
  }

  const main = document.querySelector("main");
  const nav = document.createElement("nav");
  nav.className = "topic-nav";

  const indexLink = document.createElement("a");
  indexLink.href = "index.html";
  indexLink.textContent = "Index";
  nav.appendChild(indexLink);

  const nextTopic = topics[currentIndex + 1];
  const nextLink = document.createElement("a");
  nextLink.className = "primary";
  nextLink.href = nextTopic ? nextTopic.file : "index.html";
  nextLink.textContent = nextTopic ? `Next: ${nextTopic.title}` : "Next: Index";
  nav.appendChild(nextLink);

  main.appendChild(nav);
})();
