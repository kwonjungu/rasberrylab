' 과학 실험실(Science AI Lab) - 더블클릭 런처
' 1) 서버(run_server.bat)가 안 떠 있으면 최소화로 기동
' 2) /health 가 200 줄 때까지 폴링 후 기본 브라우저로 열기
Option Explicit
Dim sh, fso, base, i, ready
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)

ready = ServerReady()
If Not ready Then
  ' 최소화 창으로 서버 기동(계속 실행됨). 검증된 cmd /c "..." 형태 사용.
  sh.Run "cmd /c " & Chr(34) & base & "\run_server.bat" & Chr(34), 7, False
End If

For i = 1 To 80
  If ServerReady() Then
    ready = True
    Exit For
  End If
  WScript.Sleep 500
Next

If ready Then
  sh.Run "http://127.0.0.1:8000/", 1, False
Else
  MsgBox "서버를 시작하지 못했어요. ScienceLab 폴더의 run_server.bat 을 직접 실행해 오류를 확인해 주세요.", _
         vbExclamation, "과학 실험실"
End If

Function ServerReady()
  Dim http
  ServerReady = False
  On Error Resume Next
  Set http = CreateObject("MSXML2.XMLHTTP")
  http.Open "GET", "http://127.0.0.1:8000/health", False
  http.Send
  If Err.Number = 0 Then
    If http.Status = 200 Then ServerReady = True
  End If
  On Error GoTo 0
End Function
