#!/usr/bin/env python3
"""
Simple exerciser for HDR40 PWM pins:
- PWM5  -> soc_gpio21_ph0 (HDR40 pin 33) -> /sys/class/pwm/pwmchip2/pwm0
- PWM7  -> soc_gpio19_pg6 (HDR40 pin 32) -> /sys/class/pwm/pwmchip3/pwm0

You typically need sudo to write to /sys/class/pwm.
"""

import argparse
import os
import sys
import time
from typing import Dict


PIN_MAP: Dict[str, Dict[str, int]] = {
    "pwm5": {"chip": 2, "channel": 0, "pin": 33, "soc": "soc_gpio21_ph0"},
    "pwm7": {"chip": 3, "channel": 0, "pin": 32, "soc": "soc_gpio19_pg6"},
}


class PWMChannel:
    def __init__(self, chip: int, channel: int) -> None:
        self.chip = chip
        self.channel = channel
        self.base = f"/sys/class/pwm/pwmchip{chip}"
        self.path = os.path.join(self.base, f"pwm{channel}")

    def _write(self, name: str, value: str) -> None:
        path = os.path.join(self.path, name)
        try:
            with open(path, "w") as f:
                f.write(value)
        except OSError as e:
            raise RuntimeError(f"Failed writing '{value}' to {path}: {e}") from e

    def export(self) -> None:
        if not os.path.isdir(self.base):
            raise RuntimeError(f"{self.base} not present")
        if not os.path.isdir(self.path):
            with open(os.path.join(self.base, "export"), "w") as f:
                f.write(str(self.channel))
            # Wait briefly for sysfs node creation
            for _ in range(5):
                if os.path.isdir(self.path):
                    break
                time.sleep(0.05)
        if not os.path.isdir(self.path):
            raise RuntimeError(f"PWM channel path missing after export: {self.path}")

    def configure(self, period_ns: int, duty_ns: int) -> None:
        if duty_ns >= period_ns:
            raise ValueError(f"duty_ns ({duty_ns}) must be < period_ns ({period_ns})")

        # Disable before reconfiguring (ignore EINVAL if already disabled)
        try:
            self._write("enable", "0")
        except RuntimeError:
            pass
        self._write("period", str(period_ns))
        self._write("duty_cycle", str(duty_ns))

    def enable(self, enable: bool) -> None:
        self._write("enable", "1" if enable else "0")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Drive Jetson Orin HDR40 PWM pins via sysfs")
    p.add_argument(
        "--pins",
        default="pwm5,pwm7",
        help="Comma list of pins to drive (choices: pwm5,pwm7)",
    )
    p.add_argument("--period-ns", type=int, default=20_000_000, help="PWM period in nanoseconds")
    p.add_argument("--duty-ns", type=int, default=1_500_000, help="PWM duty in nanoseconds")
    p.add_argument("--seconds", type=float, default=5.0, help="How long to keep PWM enabled")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    requested = [p.strip() for p in args.pins.split(",") if p.strip()]
    for pin in requested:
        if pin not in PIN_MAP:
            print(f"Unknown pin '{pin}', valid: {', '.join(PIN_MAP)}", file=sys.stderr)
            return 1

    channels = []
    for pin in requested:
        meta = PIN_MAP[pin]
        print(
            f"Configuring {pin} (HDR40 pin {meta['pin']} / {meta['soc']}) "
            f"at pwmchip{meta['chip']} channel {meta['channel']}"
        )
        ch = PWMChannel(meta["chip"], meta["channel"])
        ch.export()
        ch.configure(args.period_ns, args.duty_ns)
        channels.append(ch)

    for ch in channels:
        ch.enable(True)

    print(f"PWM running for {args.seconds} seconds (period={args.period_ns}ns duty={args.duty_ns}ns)")
    try:
        time.sleep(args.seconds)
    finally:
        for ch in channels:
            try:
                ch.enable(False)
            except Exception:
                pass
        print("PWM disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
