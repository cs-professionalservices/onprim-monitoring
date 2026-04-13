# Agent 3 Run Guide

This folder contains the prebuilt Agent 3 binaries for the `prod` and `qa`
environments.

Important:
- `--account-id` is required in every run command.
- Linux binary name: `cs_metrics_agent_linux`
- Windows binary name: `cs_metrics_agent_win.exe`
- The examples below write logs to `cs--metrics-agent.log`

## Prod

### Linux

Download:

```bash
mkdir -p ~/agent3/prod
cd ~/agent3/prod
wget -O cs_metrics_agent_linux "https://github.com/cs-professionalservices/onprim-monitoring/raw/refs/heads/main/agent3/prod/linux/cs_metrics_agent_linux"
chmod +x cs_metrics_agent_linux
```

Run in background:

```bash
nohup ./cs_metrics_agent_linux --account-id "<ACCOUNT_ID>" >> cs-metrics-agent.log 2>&1 &
```

View logs:

```bash
tail -f cs-metrics-agent.log
```

### Windows

Download:

```powershell
New-Item -ItemType Directory -Force -Path "C:\agent3\prod" | Out-Null
Set-Location "C:\agent3\prod"
wget "https://github.com/cs-professionalservices/onprim-monitoring/raw/refs/heads/main/agent3/prod/windows/dist/cs_metrics_agent_win.exe" -OutFile "cs_metrics_agent_win.exe"
```

Run in background:

```powershell
New-Item -ItemType File -Force -Path ".\cs--metrics-agent.log" | Out-Null
Start-Job -Name "cs-metrics-agent-prod" -ScriptBlock {
    Set-Location "C:\agent3\prod"
    & ".\cs_metrics_agent_win.exe" --account-id "<ACCOUNT_ID>" *>> ".\cs-metrics-agent.log"
}
```

View logs:

```powershell
Get-Content ".\cs-metrics-agent.log" -Wait
```

## QA

### Linux

Download:

```bash
mkdir -p ~/agent3/qa
cd ~/agent3/qa
wget -O cs_metrics_agent_linux "https://github.com/cs-professionalservices/onprim-monitoring/raw/refs/heads/main/agent3/qa/linux/cs_metrics_agent_linux"
chmod +x cs_metrics_agent_linux
```

Run in background:

```bash
nohup ./cs_metrics_agent_linux --account-id "<ACCOUNT_ID>" >> cs-metrics-agent.log 2>&1 &
```

View logs:

```bash
tail -f cs-metrics-agent.log
```

### Windows

Download:

```powershell
New-Item -ItemType Directory -Force -Path "C:\agent3\qa" | Out-Null
Set-Location "C:\agent3\qa"
wget "https://github.com/cs-professionalservices/onprim-monitoring/raw/refs/heads/main/agent3/qa/windows/dist/cs_metrics_agent_win.exe" -OutFile "cs_metrics_agent_win.exe"
```

Run in background:

```powershell
New-Item -ItemType File -Force -Path ".\cs--metrics-agent.log" | Out-Null
Start-Job -Name "cs-metrics-agent-qa" -ScriptBlock {
    Set-Location "C:\agent3\qa"
    & ".\cs_metrics_agent_win.exe" --account-id "<ACCOUNT_ID>" *>> ".\cs-metrics-agent.log"
}
```

View logs:

```powershell
Get-Content ".\cs-metrics-agent.log" -Wait
```

## Notes

- Replace `<ACCOUNT_ID>` with the actual account id before starting the agent.
- On Windows, `Get-Content -Wait` is the closest equivalent to `tail -f`.
- The `Start-Job` examples run the agent as a PowerShell background job for the
  current session.