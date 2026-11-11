# Profil IA - helper Windows (volume, molette, raccourcis)
# Lit une commande par ligne sur stdin, repond sur stdout.
# Commandes : get | set <0-100> | mute | wheel <crans> | zoom <crans> | zoomreset | dictee | quit
$ErrorActionPreference = 'Stop'

$code = @"
using System;
using System.Runtime.InteropServices;

namespace ProfilIA {
  [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
  interface IAudioEndpointVolume {
    int f(); int g(); int h(); int i();
    int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
    int j();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int k(); int l(); int m(); int n();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, Guid pguidEventContext);
    int GetMute(out bool pbMute);
  }
  [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
  interface IMMDevice {
    int Activate(ref Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
  }
  [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
  interface IMMDeviceEnumerator {
    int f();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
  }
  [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject { }

  public static class Audio {
    static IAudioEndpointVolume Vol() {
      var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
      IMMDevice dev = null;
      Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(0, 1, out dev));
      IAudioEndpointVolume epv = null;
      var epvid = typeof(IAudioEndpointVolume).GUID;
      Marshal.ThrowExceptionForHR(dev.Activate(ref epvid, 23, 0, out epv));
      return epv;
    }
    public static int GetVolume() { float v = 0; Marshal.ThrowExceptionForHR(Vol().GetMasterVolumeLevelScalar(out v)); return (int)Math.Round(v * 100); }
    public static void SetVolume(int pct) { if (pct < 0) pct = 0; if (pct > 100) pct = 100; Marshal.ThrowExceptionForHR(Vol().SetMasterVolumeLevelScalar(pct / 100f, Guid.Empty)); }
    public static bool GetMute() { bool m; Marshal.ThrowExceptionForHR(Vol().GetMute(out m)); return m; }
    public static void SetMute(bool m) { Marshal.ThrowExceptionForHR(Vol().SetMute(m, Guid.Empty)); }
  }

  public static class Input {
    [DllImport("user32.dll")] static extern void mouse_event(uint flags, int dx, int dy, int data, UIntPtr extra);
    [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    const uint WHEEL = 0x0800; const uint KEYUP = 0x0002;
    const byte CTRL = 0x11; const byte LWIN = 0x5B;
    public static void Wheel(int notches) { mouse_event(WHEEL, 0, 0, notches * 120, UIntPtr.Zero); }
    public static void CtrlWheel(int notches) {
      keybd_event(CTRL, 0, 0, UIntPtr.Zero);
      mouse_event(WHEEL, 0, 0, notches * 120, UIntPtr.Zero);
      keybd_event(CTRL, 0, KEYUP, UIntPtr.Zero);
    }
    public static void Combo(byte mod, byte key) {
      keybd_event(mod, 0, 0, UIntPtr.Zero);
      keybd_event(key, 0, 0, UIntPtr.Zero);
      keybd_event(key, 0, KEYUP, UIntPtr.Zero);
      keybd_event(mod, 0, KEYUP, UIntPtr.Zero);
    }
    public static void CtrlZero() { Combo(CTRL, 0x30); }
    public static void WinH() { Combo(LWIN, 0x48); }
    public static void CtrlC() { Combo(CTRL, 0x43); }
    public static void CtrlV() { Combo(CTRL, 0x56); }
    public static void Enter() { keybd_event(0x0D, 0, 0, UIntPtr.Zero); keybd_event(0x0D, 0, KEYUP, UIntPtr.Zero); }
  }

  public static class Win {
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] public static extern uint GetClipboardSequenceNumber();
    public static long Fg() { return GetForegroundWindow().ToInt64(); }
    public static string FgProc() {
      try {
        uint pid; GetWindowThreadProcessId(GetForegroundWindow(), out pid);
        return System.Diagnostics.Process.GetProcessById((int)pid).ProcessName.ToLowerInvariant();
      } catch { return ""; }
    }
  }
}
"@

Add-Type -TypeDefinition $code -Language CSharp
Add-Type -AssemblyName System.Windows.Forms

function GetClipText {
  for ($i = 0; $i -lt 5; $i++) {
    try {
      if ([System.Windows.Forms.Clipboard]::ContainsText()) { return [System.Windows.Forms.Clipboard]::GetText() }
      return $null
    } catch { Start-Sleep -Milliseconds 40 }
  }
  return $null
}
function SetClipText($t) {
  for ($i = 0; $i -lt 5; $i++) {
    try { [System.Windows.Forms.Clipboard]::SetText($t); return } catch { Start-Sleep -Milliseconds 40 }
  }
}
function FromB64($s) { [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($s)) }

function DoPrompt($id, $cfg) {
  $origFg = [ProfilIA.Win]::Fg()
  $origProc = [ProfilIA.Win]::FgProc()
  $backup = GetClipText
  $hadText = ($backup -ne $null)

  # 1. recuperer le texte
  $sel = $null
  if ($cfg.source -eq 'selection') {
    $seq = [ProfilIA.Win]::GetClipboardSequenceNumber()
    [ProfilIA.Input]::CtrlC()
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt 700) {
      if ([ProfilIA.Win]::GetClipboardSequenceNumber() -ne $seq) { break }
      Start-Sleep -Milliseconds 25
    }
    if ([ProfilIA.Win]::GetClipboardSequenceNumber() -ne $seq) { Start-Sleep -Milliseconds 60; $sel = GetClipText }
    if ((-not $sel) -and $cfg.fallback -eq 'clipboard') { $sel = $backup }
  } elseif ($cfg.source -eq 'clipboard') {
    $sel = $backup
  }
  if ($sel) { $sel = $sel.Trim() }
  $hasSel = [bool]$sel

  # 2. construire l'URL
  $prompt = [string]$cfg.prompt
  $nl = "`n`n"
  $isWeb = ($cfg.target -eq 'web' -or $cfg.target -eq 'chatgpt')
  if ($cfg.target -eq 'web') { $base = 'https://claude.ai/new' }
  elseif ($cfg.target -eq 'chatgpt') { $base = 'https://chatgpt.com/' }
  elseif ($cfg.target -eq 'code') { $base = 'claude://code/new' }
  else { $base = 'claude://claude.ai/new' }

  $needPaste = $false
  $pasteText = $null
  if ($cfg.target -eq 'code') {
    $url = $base
    if ($hasSel) { $pasteText = $prompt + $nl + $sel } else { $pasteText = $prompt }
    $needPaste = [bool]$pasteText
  } else {
    if ($hasSel) { $full = $prompt + $nl + $sel } else { $full = $prompt + $nl }
    $q = [Uri]::EscapeDataString($full)
    if ($q.Length -le 1800) { $url = $base + '?q=' + $q }
    else { $url = $base + '?q=' + [Uri]::EscapeDataString($prompt + $nl); $needPaste = $true; $pasteText = $sel }
  }

  # 3. ouvrir et attendre la fenetre
  [System.Diagnostics.Process]::Start($url) | Out-Null
  $hint = 'claude'
  if ($isWeb) { $hint = '' }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $ok = $false
  while ($sw.ElapsedMilliseconds -lt 12000) {
    $fg = [ProfilIA.Win]::Fg()
    $proc = [ProfilIA.Win]::FgProc()
    if ($fg -ne $origFg -and $fg -ne 0) { $ok = $true; break }
    if ($hint -and $proc -eq $hint -and $origProc -eq $hint) { $ok = $true; break }
    Start-Sleep -Milliseconds 50
  }
  $wait = 900
  if ($isWeb) { $wait = 2500 }
  if ($cfg.wait) { $wait = [int]$cfg.wait }
  Start-Sleep -Milliseconds $wait

  # 4. coller / envoyer
  if ($needPaste) {
    SetClipText $pasteText
    Start-Sleep -Milliseconds 80
    [ProfilIA.Input]::CtrlV()
    Start-Sleep -Milliseconds 200
  }
  $send = ($cfg.send -eq $true) -and ($hasSel -or $cfg.source -eq 'none')
  if ($send) { [ProfilIA.Input]::Enter() }

  # 5. remettre le presse-papiers
  if ($cfg.restore -ne $false -and $hadText -and $backup) {
    Start-Sleep -Milliseconds 300
    SetClipText $backup
  }
  $state = 'noselection'
  if ($hasSel) { $state = 'ok' } elseif ($cfg.source -eq 'none') { $state = 'ok' }
  if (-not $ok) { $state = 'nowindow' }
  Say ("prompt " + $id + " " + $state)
}

function Say($s) { [Console]::Out.WriteLine($s); [Console]::Out.Flush() }
function SayVol { Say ("vol " + [ProfilIA.Audio]::GetVolume() + " " + [int][ProfilIA.Audio]::GetMute()) }

Say 'ready'
while ($true) {
  $line = [Console]::In.ReadLine()
  if ($line -eq $null) { break }
  $p = $line.Trim().Split(' ')
  try {
    switch ($p[0]) {
      'get'       { SayVol }
      'set'       { [ProfilIA.Audio]::SetVolume([int]$p[1]); SayVol }
      'mute'      { [ProfilIA.Audio]::SetMute(-not [ProfilIA.Audio]::GetMute()); SayVol }
      'unmute'    { [ProfilIA.Audio]::SetMute($false); SayVol }
      'wheel'     { [ProfilIA.Input]::Wheel([int]$p[1]) }
      'zoom'      { [ProfilIA.Input]::CtrlWheel([int]$p[1]) }
      'zoomreset' { [ProfilIA.Input]::CtrlZero() }
      'dictee'    { [ProfilIA.Input]::WinH() }
      'prompt'    {
        try { DoPrompt $p[1] ((FromB64 $p[2]) | ConvertFrom-Json) }
        catch { Say ("prompt " + $p[1] + " error " + $_.Exception.Message) }
      }
      'quit'      { exit 0 }
      default     { }
    }
  } catch {
    Say ('err ' + $_.Exception.Message)
  }
}
