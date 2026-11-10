Option Explicit
Dim WshShell, Http, AlreadyOnline
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\.skill-registry"

' Verifica se o J.A.R.V.I.S. já está online na porta 8899 para nunca abrir processos duplicados
AlreadyOnline = False
On Error Resume Next
Set Http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
Http.setTimeouts 400, 400, 400, 400
Http.Open "GET", "http://127.0.0.1:8899/favicon.ico", False
Http.Send
If Err.Number = 0 And (Http.Status = 200 Or Http.Status = 204 Or Http.Status = 403) Then
    AlreadyOnline = True
End If
On Error GoTo 0

If Not AlreadyOnline Then
    ' Inicia o J.A.R.V.I.S. Resident Host de forma 100% invisível em segundo plano
    WshShell.Run """C:\Users\Ad\AppData\Local\Programs\Python\Python312\pythonw.exe"" ""E:\.skill-registry\state\remote_service\jarvis_remote_host.pyw""", 0, False
    ' Aguarda o servidor responder 200 na porta 8899 antes de abrir o navegador
    Dim attempt
    For attempt = 1 To 15
        WScript.Sleep 500
        On Error Resume Next
        Http.Open "GET", "http://127.0.0.1:8899/favicon.ico", False
        Http.Send
        If Err.Number = 0 And (Http.Status = 200 Or Http.Status = 204 Or Http.Status = 403) Then
            Exit For
        End If
        On Error GoTo 0
    Next
End If

' Abre o HUD no Google Chrome no perfil Roberto
Dim Fso, ChromePath
Set Fso = CreateObject("Scripting.FileSystemObject")
ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
If Fso.FileExists(ChromePath) Then
    WshShell.Run """" & ChromePath & """ --profile-directory=""Profile 2"" --new-window ""http://127.0.0.1:8899/""", 1, False
Else
    WshShell.Run "http://127.0.0.1:8899/", 1, False
End If
