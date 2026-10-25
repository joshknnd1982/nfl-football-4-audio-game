; Inno Setup 6 script: NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen (nfl4).
; Phase 10 (playbook 8.2); this file is nfl4's since S8.2 (a test installer). Compile (from anywhere):
;   "C:\Users\joshk\AppData\Local\Programs\Inno Setup 6\ISCC.exe" "<game folder>\release\installer.iss"
; Optional defines: /DAppVersion=0.9.0  /DBuild64=<dist\nfl4 folder>  /DBuild32=<dist\nfl4 folder>
; Run game\tools\build.ps1 first so the build folders are fresh. Output: nfl4-setup-<version>.exe in this folder.
;
; Design decisions (DECISIONS.md, P10):
;  - One installer holds both builds and installs the one that fits the Windows (64-bit or 32-bit).
;  - Per-user install by default (no administrator rights); the player may choose all users in the first dialog.
;  - The program folder holds only program files. Settings, player sounds and logs live in
;    %APPDATA%\Kitchensinc Revival\NFL Football 4; install, update and uninstall never touch them
;    (the uninstaller asks, default keep).
;  - An update removes the old _internal folder first (stale library files), never assets\sounds' extras.
;  - Uninstall removes the WHOLE program folder: it stops a copy that is still running from that folder, deletes the
;    folder with retries and leaves the rest to a restart-delete (fixesforgames.md B-U1, B-U2).

#ifndef AppVersion
  #define AppVersion "0.9.0"
#endif
#ifndef Build64
  #define Build64 "C:\Users\joshk\.kitchensinc-builds\nfl4\64\dist\nfl4"
#endif
#ifndef Build32
  #define Build32 "C:\Users\joshk\.kitchensinc-builds\nfl4\32\dist\nfl4"
#endif

[Setup]
; Never change this GUID: it is how a newer version finds and replaces an older one.
AppId={{BB3ABD62-0DFC-4990-955C-904410D53800}
AppName=NFL Football 4
AppVersion={#AppVersion}
AppVerName=NFL Football 4 {#AppVersion}
AppPublisher=Josh Kennedy
AppPublisherURL=https://github.com/joshknnd1982
AppSupportURL=https://github.com/joshknnd1982
AppUpdatesURL=https://github.com/joshknnd1982
VersionInfoVersion={#AppVersion}
VersionInfoDescription=NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen (setup)
VersionInfoCopyright=Copyright (c) 2026 Josh Kennedy
DefaultDirName={autopf}\NFL Football 4
DefaultGroupName=NFL Football 4
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=.
OutputBaseFilename=nfl4-setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
LicenseFile=..\LICENSE
InfoBeforeFile=installer_info.txt
UninstallDisplayName=NFL Football 4
UninstallDisplayIcon={app}\nfl4.exe
CloseApplications=yes
RestartApplications=no
ShowLanguageDialog=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[InstallDelete]
; Library files of an older build that this build no longer has. Only our own folder.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
; uninsrestartdelete: a file still in use when the uninstaller runs is removed at the next restart (last resort only).
Source: "{#Build64}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion uninsrestartdelete; Check: Is64BitInstallMode
Source: "{#Build32}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion uninsrestartdelete; Check: not Is64BitInstallMode

[Icons]
; WorkingDir is a neutral folder, never the program folder: a process whose working directory is inside a folder keeps
; that folder locked ("folder in use") even when nothing shows in Task Manager (fixesforgames.md B-U1).
Name: "{group}\NFL Football 4"; Filename: "{app}\nfl4.exe"; WorkingDir: "{userdocs}"
Name: "{group}\NFL Football 4 read me"; Filename: "{app}\README.txt"
Name: "{group}\Uninstall NFL Football 4"; Filename: "{uninstallexe}"; WorkingDir: "{userdocs}"
Name: "{autodesktop}\NFL Football 4"; Filename: "{app}\nfl4.exe"; WorkingDir: "{userdocs}"; Tasks: desktopicon

[Run]
Filename: "{app}\nfl4.exe"; Description: "Start NFL Football 4 now"; WorkingDir: "{userdocs}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallDelete]
; The whole program folder: nothing of the program is meant to stay in it (settings, own sounds and the log are in AppData).
Type: filesandordirs; Name: "{app}"

[Code]
// Uninstall: the program goes, the player's settings, own sounds and log stay unless the player says yes.
// Silent uninstall keeps them too, unless the command line has /DELETEUSERDATA=1 (used by the scripted tests).
// {param:} is not expanded inside the uninstaller, so the command line is read by hand.
function WantsDeleteUserData: Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/DELETEUSERDATA=1') = 0 then Result := True;
end;

// ----- The program folder must go completely, and at once (owner bug 2026-10-13: "My Brain" was left in Program Files
// and then "folder in use" until a restart). A copy that is still running is stopped before files are removed; the
// folder is removed with retries because a virus scanner or Explorer can hold a file for a moment; whatever is still
// in use after that is removed at the next restart by the uninsrestartdelete flag of [Files].
function PowerShellExe: String;
begin
  if IsWin64 then
    Result := ExpandConstant('{sysnative}\WindowsPowerShell\v1.0\powershell.exe')   // the 32-bit uninstaller must start the 64-bit PowerShell to see 64-bit processes
  else
    Result := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
end;

procedure StopRunningCopies;
var
  ResultCode: Integer;
  Folder: String;
begin
  // Only processes whose program file is inside the folder being removed (a portable copy elsewhere is left alone).
  // The uninstaller's own first-phase process (unins000.exe, still waiting) is not touched: killing it made the
  // uninstaller report exit code -1 although the uninstall had worked.
  Folder := RemoveBackslash(ExpandConstant('{app}'));
  StringChangeEx(Folder, '''', '''''', True);          // a quote in the path must not end the PowerShell string
  Exec(PowerShellExe,
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "Get-Process | Where-Object { $_.Path -and $_.ProcessName -notlike ''unins*'' -and $_.Path.StartsWith(''' +
    Folder + '\'', [System.StringComparison]::OrdinalIgnoreCase) } | Stop-Process -Force"',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(800);                                          // handles are released a moment after a process has ended
end;

procedure RemoveFolderWithRetries(Folder: String);
var
  I: Integer;
begin
  // Used for the program folder and for the settings folder: a virus scanner or the indexer can hold a file for a moment
  // (one scripted verification run once left the settings folder behind after the "delete my settings" uninstall).
  for I := 1 to 20 do
  begin
    if not DirExists(Folder) then Exit;
    DelTree(Folder, True, True, True);
    if not DirExists(Folder) then Exit;
    Sleep(500);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir, Vendor: String;
  DoDelete: Boolean;
begin
  if CurUninstallStep = usUninstall then
  begin
    StopRunningCopies;
    Exit;
  end;
  if CurUninstallStep <> usPostUninstall then Exit;
  RemoveFolderWithRetries(ExpandConstant('{app}'));
  Vendor := ExpandConstant('{userappdata}\Kitchensinc Revival');
  DataDir := Vendor + '\NFL Football 4';
  if not DirExists(DataDir) then Exit;
  DoDelete := WantsDeleteUserData;
  if (not DoDelete) and (not UninstallSilent) then
    DoDelete := MsgBox('Also delete your NFL Football 4 settings, your own sounds and the log?' + #13#10 + #13#10 +
      'They are in ' + DataDir + #13#10 + #13#10 +
      'Choose No to keep them (recommended if you may install NFL Football 4 again).',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
  if DoDelete then
  begin
    RemoveFolderWithRetries(DataDir);
    RemoveDir(Vendor);   // only if nothing else (another Kitchensinc game) is in it
  end;
end;
