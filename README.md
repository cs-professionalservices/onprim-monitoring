# 📦 Metrics Collector – Run Guide

This package contains pre-built executables for **Linux** and **Windows**.
No installation required.

---

## 🐧 Linux (RHEL / Rocky / Ubuntu)

### Copy file to server

```bash
scp psutil_onprem_metric csadmin@<SERVER_IP>:~/metrics_collector/
```

If folder doesn’t exist:

```bash
ssh csadmin@<SERVER_IP> "mkdir -p ~/metrics_collector"
```

---

### Run on server

```bash
ssh csadmin@<SERVER_IP>
cd ~/metrics_collector
chmod +x psutil_onprem_metric
```

---

### Run in background

```bash
nohup ./psutil_onprem_metric > collector.log 2>&1 &
```

---

### Verify running

```bash
pgrep -fl psutil_onprem_metric
```

---

### Check logs

```bash
tail -f collector.log
```

---

### Stop process

```bash
pkill -f psutil_onprem_metric
```

---

## 🪟 Windows

### Run executable

Double-click:

```
psutil_onprem_metric.exe
```

OR via terminal:

```powershell
.\psutil_onprem_metric.exe
```

---

### Run in background

```powershell
Start-Process .\psutil_onprem_metric.exe
```

---

### Stop process

```powershell
taskkill /IM psutil_onprem_metric.exe /F
```

---

## Files

```
psutil_onprem_metric        → Linux binary
psutil_onprem_metric.exe    → Windows executable
```

---

## Notes

* No Python or dependencies required
* Works as standalone binary
* Logs written to `collector.log` (Linux)

---

## Done

Just copy → run → monitor
