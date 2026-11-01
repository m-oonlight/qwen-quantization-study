#!/usr/bin/env bash
set -eu
# Run once with sudo. Only enables read access to CPU energy counters for cs4's group.
[ "$(id -u)" = 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
cat > /etc/udev/rules.d/80-qwen-cpu-energy.rules <<'RULE'
ACTION=="add", SUBSYSTEM=="powercap", KERNEL=="intel-rapl:*", RUN+="/usr/bin/chgrp cs4 /sys%p/energy_uj", RUN+="/usr/bin/chmod g+r /sys%p/energy_uj"
RULE
udevadm control --reload-rules
for counter in /sys/class/powercap/intel-rapl:*/energy_uj; do
 [ -f "$counter" ] || continue
 chgrp cs4 "$counter"
 chmod g+r "$counter"
done
echo 'CPU energy counters are group-readable; udev rule installed for future boots.'
