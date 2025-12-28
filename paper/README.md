# Paper artifacts

This folder holds the fork-specific overlays and scripts used for the paper while keeping the upstream layout intact.

## Layout
- `overlays/src/` : DTS sources (all-pins GPIO, expanded pin7, and the `_check` fragment).
- `overlays/build/` : Prebuilt DTBOs. Files without suffix come from `overlays/src`; files ending in `.root.dtbo` are the earlier root-level binaries preserved for reference.
- `examples/` : Custom scripts (multi-pin `simple_out`, PWM exerciser, gpiod toggle).

## Rebuild DTBOs
From the repo root:
```bash
dtc -O dtb -o paper/overlays/build/<name>.dtbo paper/overlays/src/<name>.dts
```

PWM scripts write to `/sys/class/pwm`; you typically need `sudo`.
