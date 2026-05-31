Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = projectDir & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    MsgBox "Virtual environment not found. Run these commands first:" & vbCrLf & vbCrLf & _
        "python -m venv .venv" & vbCrLf & _
        ".\.venv\Scripts\Activate.ps1" & vbCrLf & _
        "pip install -e .", vbExclamation, "lol-im-afk"
    WScript.Quit 1
End If

shell.CurrentDirectory = projectDir
shell.Run """" & pythonw & """ -m lol_im_afk --tray", 0, False
