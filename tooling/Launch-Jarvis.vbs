' ==============================================================================
' J.A.R.V.I.S. Sovereign Desktop Launcher (Native Desktop App Window / SAPI)
' ==============================================================================

Option Explicit
Dim wsh, http, fso, serverUrl, serverScript, isRunning, waitedMs, pollHttp
Dim pythonwPath, pyCmd, chromePath, edgePath, appCmd, profileDir

Set wsh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
serverUrl = "http://localhost:8899/api/status"
serverScript = "E:\.skill-registry\tooling\jarvis_server.py"
pythonwPath = "C:\Users\Ad\AppData\Local\Programs\Python\Python312\pythonw.exe"
profileDir = "E:\.skill-registry\ui\.jarvis-profile"

' 1. Check if server is already running
isRunning = False
On Error Resume Next
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
http.setTimeouts 600, 600, 600, 600
http.open "GET", serverUrl, False
http.send
If http.status = 200 Then
    isRunning = True
End If
On Error GoTo 0

' 2. If server is not running, launch it completely silent via Python 3.12 (WindowStyle = 0)
If Not isRunning Then
    pyCmd = """" & pythonwPath & """ """ & serverScript & """ --port 8899"
    wsh.Run pyCmd, 0, False

    ' Active polling: wait up to 15 seconds for server to be fully ready
    waitedMs = 0
    Do While waitedMs < 15000 And Not isRunning
        WScript.Sleep 350
        waitedMs = waitedMs + 350
        On Error Resume Next
        Set pollHttp = CreateObject("MSXML2.ServerXMLHTTP.6.0")
        pollHttp.setTimeouts 500, 500, 500, 500
        pollHttp.open "GET", serverUrl, False
        pollHttp.send
        If pollHttp.status = 200 Then
            isRunning = True
        End If
        On Error GoTo 0
    Loop
End If

' 3. Subtle tactical acoustic chime
On Error Resume Next
wsh.Run "powershell.exe -NoProfile -Command ""[System.Media.SystemSounds]::Asterisk.Play()""", 0, False
On Error GoTo 0

' 4. Single-Instance Enforcement: if healthy J.A.R.V.I.S. window exists, activate it
If wsh.AppActivate("J.A.R.V.I.S.") Then
    WScript.Quit
End If

' If there is a stuck/stale browser window on localhost:8899 (e.g. ERR_CONNECTION_REFUSED error tab), clean it up
Dim objWMI, colProcs, procItem
On Error Resume Next
Set objWMI = GetObject("winmgmts:\\.\root\cimv2")
Set colProcs = objWMI.ExecQuery("Select ProcessId from Win32_Process Where CommandLine Like '%localhost:8899%' and (Name = 'chrome.exe' or Name = 'msedge.exe')")
For Each procItem in colProcs
    procItem.Terminate()
Next
On Error GoTo 0

' 5. Rapid double-click lockfile check (< 3.5 seconds)
Dim lockPath, lockFile
lockPath = fso.GetSpecialFolder(2) & "\jarvis_launch.lock"
If fso.FileExists(lockPath) Then
    Dim fObj, ageSec
    Set fObj = fso.GetFile(lockPath)
    ageSec = DateDiff("s", fObj.DateLastModified, Now())
    If ageSec < 3 Then
        WScript.Quit
    End If
End If

On Error Resume Next
Set lockFile = fso.CreateTextFile(lockPath, True)
lockFile.WriteLine CStr(Now())
lockFile.Close
On Error GoTo 0

' 6. Open in NATIVE DESKTOP APP MODE (Standalone window without address bar or tabs)
chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

If fso.FileExists(chromePath) Then
    wsh.Run """" & chromePath & """ --app=http://localhost:8899/ --window-size=1440,920", 1, False
ElseIf fso.FileExists(edgePath) Then
    wsh.Run """" & edgePath & """ --app=http://localhost:8899/ --window-size=1440,920", 1, False
Else
    wsh.Run "http://localhost:8899/", 1, False
End If
