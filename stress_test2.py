#!/usr/bin/env python3
"""
Real-world style VM variation load generator.

It runs in burst windows (default 20-25 seconds) and randomly changes load
profile each burst to mimic non-uniform production behavior.

Examples:
  python vm_realworld_variation_test.py --duration 900
  python vm_realworld_variation_test.py --duration 600 --workers 6
  python vm_realworld_variation_test.py --duration 1200 --seed 42
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import random
import socket
import sys
import time
from typing import Dict, List


def _cpu_worker(stop_at: float, duty_cycle: float) -> None:
    duty = max(0.0, min(1.0, duty_cycle))
    cycle_sec = 0.1
    busy_sec = cycle_sec * duty
    idle_sec = cycle_sec - busy_sec

    while time.time() < stop_at:
        t_end = time.perf_counter() + busy_sec
        while time.perf_counter() < t_end:
            pass
        if idle_sec > 0:
            time.sleep(idle_sec)


def _memory_noise(stop_at: float, chunks: int, chunk_mb: int) -> None:
    data: List[bytearray] = []
    chunk_bytes = max(1, chunk_mb) * 1024 * 1024
    chunks = max(0, chunks)
    try:
        for _ in range(chunks):
            if time.time() >= stop_at:
                break
            data.append(bytearray(chunk_bytes))
            # Touch memory so it is committed.
            data[-1][0] = 1
    except MemoryError:
        pass
    while time.time() < stop_at:
        if data:
            idx = random.randint(0, len(data) - 1)
            data[idx][0] = (data[idx][0] + 1) % 255
        time.sleep(0.05)


def _disk_noise(stop_at: float, file_path: str, mb_per_burst: int) -> None:
    mb_per_burst = max(1, mb_per_burst)
    block = os.urandom(1024 * 1024)  # 1 MB
    try:
        with open(file_path, "wb") as fh:
            while time.time() < stop_at:
                for _ in range(mb_per_burst):
                    if time.time() >= stop_at:
                        break
                    fh.write(block)
                fh.flush()
                os.fsync(fh.fileno())
    except Exception:
        pass
    finally:
        try:
            os.remove(file_path)
        except Exception:
            pass


def _network_noise(stop_at: float, packets_per_sec: int, packet_size: int) -> None:
    packets_per_sec = max(1, packets_per_sec)
    packet_size = max(64, packet_size)
    payload = b"x" * packet_size
    target = ("127.0.0.1", 9999)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
    except Exception:
        return

    interval = 1.0 / float(packets_per_sec)
    next_send = time.perf_counter()
    try:
        while time.time() < stop_at:
            now = time.perf_counter()
            if now >= next_send:
                try:
                    sock.sendto(payload, target)
                except Exception:
                    pass
                next_send += interval
            else:
                time.sleep(min(0.005, next_send - now))
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _random_profile(rng: random.Random, workers: int) -> Dict[str, float]:
    # Weighted CPU levels: mostly low/medium with occasional spikes.
    r = rng.random()
    if r < 0.55:
        cpu_target = rng.uniform(10, 40)
    elif r < 0.85:
        cpu_target = rng.uniform(40, 75)
    else:
        cpu_target = rng.uniform(75, 95)

    # Active workers vary by profile.
    active_ratio = rng.uniform(0.3, 1.0)
    active_workers = max(1, int(round(workers * active_ratio)))

    # Optional side noise (kept lightweight by default).
    mem_chunks = rng.randint(0, 8)     # each chunk is chunk_mb
    chunk_mb = rng.choice([2, 4, 8])
    disk_mb = rng.choice([1, 2, 4, 8])
    pps = rng.choice([50, 100, 250, 500])
    pkt_size = rng.choice([128, 256, 512, 1024])

    return {
        "cpu_target": cpu_target,
        "active_workers": float(active_workers),
        "mem_chunks": float(mem_chunks),
        "chunk_mb": float(chunk_mb),
        "disk_mb": float(disk_mb),
        "pps": float(pps),
        "pkt_size": float(pkt_size),
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate random, bursty VM load.")
    p.add_argument("--duration", type=int, default=900, help="Total test duration (seconds).")
    p.add_argument("--workers", type=int, default=0, help="CPU worker pool size (default: logical CPUs).")
    p.add_argument("--burst-min", type=int, default=20, help="Minimum burst window seconds.")
    p.add_argument("--burst-max", type=int, default=25, help="Maximum burst window seconds.")
    p.add_argument("--report-interval", type=int, default=5, help="Status report interval seconds.")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducible runs.")
    p.add_argument("--no-memory-noise", action="store_true", help="Disable memory noise.")
    p.add_argument("--no-disk-noise", action="store_true", help="Disable disk noise.")
    p.add_argument("--no-network-noise", action="store_true", help="Disable network noise.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    duration = max(1, int(args.duration))
    workers = int(args.workers) if int(args.workers) > 0 else (os.cpu_count() or 1)
    burst_min = max(1, int(args.burst_min))
    burst_max = max(burst_min, int(args.burst_max))
    report_interval = max(1, int(args.report_interval))
    rng = random.Random(args.seed)

    overall_end = time.time() + duration
    burst_idx = 0

    print("Starting real-world variation VM test")
    print(f"  duration         : {duration}s")
    print(f"  workers pool     : {workers}")
    print(f"  burst window     : {burst_min}-{burst_max}s")
    print(f"  memory noise     : {'off' if args.no_memory_noise else 'on'}")
    print(f"  disk noise       : {'off' if args.no_disk_noise else 'on'}")
    print(f"  network noise    : {'off' if args.no_network_noise else 'on'}")
    if args.seed is not None:
        print(f"  seed             : {args.seed}")
    print("Press Ctrl+C to stop.")

    try:
        while time.time() < overall_end:
            burst_idx += 1
            burst_len = rng.randint(burst_min, burst_max)
            burst_stop = min(overall_end, time.time() + burst_len)
            profile = _random_profile(rng, workers)

            active_workers = int(profile["active_workers"])
            cpu_target = float(profile["cpu_target"])
            duty = cpu_target / 100.0

            procs: List[mp.Process] = []
            for _ in range(active_workers):
                p = mp.Process(target=_cpu_worker, args=(burst_stop, duty), daemon=True)
                p.start()
                procs.append(p)

            if not args.no_memory_noise:
                p = mp.Process(
                    target=_memory_noise,
                    args=(burst_stop, int(profile["mem_chunks"]), int(profile["chunk_mb"])),
                    daemon=True,
                )
                p.start()
                procs.append(p)

            if not args.no_disk_noise:
                temp_name = f"vm_variation_disk_{os.getpid()}_{burst_idx}.bin"
                temp_path = os.path.join(os.getcwd(), temp_name)
                p = mp.Process(
                    target=_disk_noise,
                    args=(burst_stop, temp_path, int(profile["disk_mb"])),
                    daemon=True,
                )
                p.start()
                procs.append(p)

            if not args.no_network_noise:
                p = mp.Process(
                    target=_network_noise,
                    args=(burst_stop, int(profile["pps"]), int(profile["pkt_size"])),
                    daemon=True,
                )
                p.start()
                procs.append(p)

            print(
                f"[burst {burst_idx:03d}] len={int(burst_stop - time.time())}s "
                f"cpu_target={cpu_target:4.1f}% workers={active_workers} "
                f"mem_chunks={int(profile['mem_chunks'])} chunk_mb={int(profile['chunk_mb'])} "
                f"disk_mb={int(profile['disk_mb'])} pps={int(profile['pps'])}"
            )

            while time.time() < burst_stop:
                remaining_total = int(max(0, overall_end - time.time()))
                remaining_burst = int(max(0, burst_stop - time.time()))
                print(
                    f"  remaining total={remaining_total}s burst={remaining_burst}s",
                    flush=True,
                )
                time.sleep(min(report_interval, max(1, remaining_burst)))

            for p in procs:
                if p.is_alive():
                    p.terminate()
            for p in procs:
                p.join(timeout=1)

    except KeyboardInterrupt:
        print("Interrupted. Stopping...")

    print("Variation test finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

