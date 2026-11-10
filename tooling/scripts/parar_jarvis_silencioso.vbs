Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\.skill-registry"
' Para o resident host do J.A.R.V.I.S. através do endpoint local de controle
WshShell.Run """C:\Users\Ad\AppData\Local\Programs\Python\Python312\python.exe"" ""E:\.skill-registry\jarvis.py"" service stop", 0, False
