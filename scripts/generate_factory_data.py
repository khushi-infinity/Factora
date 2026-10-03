#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the deterministic synthetic factory dataset for Factora.

Writes eight CSVs into data/generated/ (plus a manifest.json):

    machines.csv               24 machines across 5 lines, twin x/y/z, status, health
    sensor_readings.csv        ~11k telemetry rows over the last 16 days, all machines
                               (hourly; CNC-03 at 10-minute cadence - its demo series)
    maintenance_history.csv    ~120-146 past faults/repairs/inspections over ~18 months
    spare_parts.csv            40-line part pool incl. BRG-AX-17 (CNC-03 bearing, limited stock)
    work_orders.csv            50-100 orders: completed / in-progress / scheduled / proposed
    production_runs.csv        14 machine-days per machine (target vs actual, OEE inputs)
    downtime_events.csv        50-100 downtime causes/durations, incl. planned + one open event
    maintenance_knowledge.csv  hand-written manual/SOP/repair-note chunks for Cortex Search

Everything except the AI4I 2020 file in data/raw/ is SYNTHETIC and labelled as such in
data/README.md. Determinism contract (AGENTS verification protocol - "same seed -> same
output"):

  * one master seed (SEED) with an independent RNG per domain, derived by SHA-256;
  * a fixed AS_OF date - the dataset never reads the wall clock, so re-runs are
    byte-identical today and in a year;
  * no dict/set iteration order leaks into output (pools are ordered lists).

Built-in consistency: every machine/part id referenced anywhere exists and is compatible;
downtime events reconcile with production_runs.downtime_minutes; completed work orders
pair 1:1 with maintenance_history rows; the CNC-03 degradation scenario is asserted
(rising vibration + temperature, CRITICAL snapshot status, one PROPOSED work order for
BRG-AX-17, two prior bearing repairs in history).

Usage:
    python3 scripts/generate_factory_data.py            # generate + validate
    python3 scripts/generate_factory_data.py --verify   # regenerate to a temp dir and
                                                        # byte-compare with data/generated
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from random import Random

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "generated"
GENERATOR_PATH = Path(__file__).resolve()

SEED = 20261003

# The dataset's fixed "as of" snapshot instant. Deliberately a constant, not now():
# determinism beats freshness for a dataset that must regenerate identically.
AS_OF = datetime(2026, 10, 3, 0, 0, 0)
READINGS_START = AS_OF - timedelta(days=16)          # 2026-09-17T00:00 (16-day window)
RUNS_START = AS_OF - timedelta(days=13)              # production window: 14 days

# Scripted CNC-03 bearing-degradation scenario (see data/README.md for the full arc).
DEMO_MACHINE = "CNC-03"
DEGRADATION_START = AS_OF - timedelta(days=5)        # healthy baseline before this
DEGRADATION_HOURS = 120.0                            # ramp ends exactly at AS_OF

MACHINE_STATES = ["HEALTHY", "WARNING", "CRITICAL", "MAINTENANCE", "OFFLINE"]


# --------------------------------------------------------------------------- helpers
def make_rng(domain: str) -> Random:
    """Independent, reproducible RNG per domain: seed + domain -> SHA-256 -> Random."""
    digest = hashlib.sha256(f"{SEED}:{domain}".encode()).digest()
    return Random(int.from_bytes(digest[:8], "big"))


def parse_ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S")


def write_csv(path: Path, header: list[str], rows: list[list]) -> int:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return len(rows)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pick(rng: Random, pool: list) -> object:
    return pool[rng.randrange(len(pool))]


# --------------------------------------------------------------------------- machines
# (machine_id, line, type, label, manufacturer, model, installed, x_m, y_m)
# One row per machine; z is 0.0 for every machine (single-floor plant, x/y in metres).
MACHINE_LAYOUT = [
    # CNC line - 8 machining centres (row y=18). CNC-03 is the demo machine.
    ("CNC-01", "CNC_LINE", "CNC", "CNC Machining Center 1", "DMG MORI", "DMU 50", 2019, 6, 18),
    ("CNC-02", "CNC_LINE", "CNC", "CNC Machining Center 2", "DMG MORI", "DMU 50", 2019, 15, 18),
    ("CNC-03", "CNC_LINE", "CNC", "CNC Machining Center 3", "Haas", "VF-4SS", 2018, 24, 18),
    ("CNC-04", "CNC_LINE", "CNC", "CNC Machining Center 4", "Haas", "VF-4SS", 2018, 33, 18),
    ("CNC-05", "CNC_LINE", "CNC", "CNC Turning Center 1", "Mazak", "QT-250", 2020, 42, 18),
    ("CNC-06", "CNC_LINE", "CNC", "CNC Turning Center 2", "Mazak", "QT-250", 2020, 51, 18),
    ("CNC-07", "CNC_LINE", "CNC", "CNC Machining Center 5", "Okuma", "Genos M560", 2021, 60, 18),
    ("CNC-08", "CNC_LINE", "CNC", "CNC Machining Center 6", "Okuma", "Genos M560", 2021, 69, 18),
    # Press line - 4 hydraulic presses (row y=34)
    ("PRS-01", "PRESS_LINE", "PRESS", "Hydraulic Press 1", "Schuler", "PH 315", 2017, 10, 34),
    ("PRS-02", "PRESS_LINE", "PRESS", "Hydraulic Press 2", "Schuler", "PH 315", 2017, 19, 34),
    ("PRS-03", "PRESS_LINE", "PRESS", "Hydraulic Press 3", "Enerpac", "IPM2500", 2016, 28, 34),
    ("PRS-04", "PRESS_LINE", "PRESS", "Hydraulic Press 4", "Dake", "B-650", 2019, 37, 34),
    # Assembly line - 5 robotic cells (row y=2)
    ("ASM-01", "ASSEMBLY_LINE", "ASSEMBLY", "Assembly Robot Cell 1", "Fanuc", "M-20iD", 2020, 8, 2),
    ("ASM-02", "ASSEMBLY_LINE", "ASSEMBLY", "Assembly Robot Cell 2", "Fanuc", "M-20iD", 2020, 16, 2),
    ("ASM-03", "ASSEMBLY_LINE", "ASSEMBLY", "Assembly Robot Cell 3", "ABB", "IRB 4600", 2021, 24, 2),
    ("ASM-04", "ASSEMBLY_LINE", "ASSEMBLY", "Assembly Robot Cell 4", "ABB", "IRB 4600", 2021, 32, 2),
    ("ASM-05", "ASSEMBLY_LINE", "ASSEMBLY", "Assembly Robot Cell 5", "KUKA", "KR CYBERTECH", 2022, 40, 2),
    # Packaging line - 4 machines (row y=50); PKG-04 is offline in the snapshot
    ("PKG-01", "PACKAGING_LINE", "PACKAGING", "Case Packer 1", "Bosch", "Sigpack TTM", 2019, 12, 50),
    ("PKG-02", "PACKAGING_LINE", "PACKAGING", "Palletizer 1", "Fanuc", "M-410iC", 2020, 21, 50),
    ("PKG-03", "PACKAGING_LINE", "PACKAGING", "Stretch Wrapper 1", "Lantech", "Q300", 2018, 30, 50),
    ("PKG-04", "PACKAGING_LINE", "PACKAGING", "Labeler 1", "Videojet", "2380", 2017, 39, 50),
    # Quality stations - 3 (row y=66)
    ("QLT-01", "QUALITY_LINE", "QUALITY", "CMM Station 1", "Zeiss", "CONTURA", 2019, 14, 66),
    ("QLT-02", "QUALITY_LINE", "QUALITY", "Vision Inspection 1", "Keyence", "CV-X", 2021, 26, 66),
    ("QLT-03", "QUALITY_LINE", "QUALITY", "CMM Station 2", "Mitutoyo", "CRYSTA", 2020, 38, 66),
]

# Snapshot statuses at AS_OF (the degradation scenario itself lives in sensor_readings):
# 20 HEALTHY, 1 WARNING (CNC-06), 1 CRITICAL (CNC-03), 1 MAINTENANCE (PRS-03), 1 OFFLINE (PKG-04).
MACHINE_STATUS = {
    "CNC-03": "CRITICAL",
    "CNC-06": "WARNING",
    "PRS-03": "MAINTENANCE",
    "PKG-04": "OFFLINE",
}

# Health-score overrides for the story machines; every other non-offline machine gets a
# deterministic score in 86-97 (healthy band). OFFLINE machines carry no score (empty).
HEALTH_OVERRIDES = {"CNC-03": 42, "CNC-06": 74, "PRS-03": 81}

# Baseline telemetry per machine type: vibration rms (mm/s), bearing temp (C),
# spindle speed (rpm), motor current (A), coolant pressure (bar), cycle time (s).
BASELINES = {
    "CNC":       {"vib": 2.4, "temp": 62.0, "rpm": 8500, "amp": 22.0, "cool": 6.2, "cycle": 118.0},
    "PRESS":     {"vib": 3.1, "temp": 55.0, "rpm": 520,  "amp": 48.0, "cool": 4.0, "cycle": 6.5},
    "ASSEMBLY":  {"vib": 1.8, "temp": 48.0, "rpm": 2100, "amp": 12.0, "cool": 0.0, "cycle": 34.0},
    "PACKAGING": {"vib": 2.8, "temp": 50.0, "rpm": 1400, "amp": 15.0, "cool": 0.0, "cycle": 3.2},
    "QUALITY":   {"vib": 0.9, "temp": 41.0, "rpm": 900,  "amp": 9.0,  "cool": 0.0, "cycle": 42.0},
}

CYCLE_TIME_S = {m[0]: BASELINES[m[2]]["cycle"] for m in MACHINE_LAYOUT}


def build_machines() -> tuple[list[str], list[list]]:
    header = ["machine_id", "name", "line", "type", "manufacturer", "model",
              "installed_year", "status", "health_score", "x_m", "y_m", "z_m"]
    rows = []
    for mid, line, mtype, label, maker, model, year, x, y in MACHINE_LAYOUT:
        status = MACHINE_STATUS.get(mid, "HEALTHY")
        if status == "OFFLINE":
            health = ""
        elif mid in HEALTH_OVERRIDES:
            health = HEALTH_OVERRIDES[mid]
        else:
            health = make_rng(f"health:{mid}").randint(86, 97)
        rows.append([mid, label, line, mtype, maker, model, year, status, health, x, y, 0.0])
    return header, rows


# -------------------------------------------------------------------- sensor_readings
def build_sensor_readings() -> tuple[list[str], list[list], dict]:
    """Telemetry for every machine over the last 16 days: hourly for all machines,
    10-minute cadence for CNC-03 so the degradation ramp charts smoothly. Returns the
    table plus the scenario summary embedded into the manifest."""
    header = ["reading_id", "machine_id", "ts", "vibration_rms_mm_s", "bearing_temp_c",
              "spindle_speed_rpm", "motor_current_a", "coolant_pressure_bar", "cycle_time_s"]

    rows: list[list] = []
    seq = 0
    for mid, _line, mtype, *_rest in MACHINE_LAYOUT:
        base = BASELINES[mtype]
        rng = make_rng(f"sensor:{mid}")
        status = MACHINE_STATUS.get(mid, "HEALTHY")
        step = timedelta(minutes=10) if mid == DEMO_MACHINE else timedelta(hours=1)
        moment = READINGS_START
        while moment < AS_OF:
            hour = moment.hour + moment.minute / 60.0
            diurnal = 0.9 * math.sin(2 * math.pi * (hour - 6) / 24)
            vib = base["vib"] + rng.gauss(0, 0.12)
            temp = base["temp"] + diurnal + rng.gauss(0, 0.8)
            rpm = base["rpm"] + rng.gauss(0, base["rpm"] * 0.015)
            amp = base["amp"] + rng.gauss(0, base["amp"] * 0.04)
            cool = base["cool"] + (rng.gauss(0, 0.12) if base["cool"] else 0.0)
            cycle = base["cycle"] + rng.gauss(0, base["cycle"] * 0.02)

            if mid == DEMO_MACHINE:
                elapsed = (moment - DEGRADATION_START).total_seconds() / 3600.0
                if elapsed > 0:
                    f = min(elapsed / DEGRADATION_HOURS, 1.0)
                    vib += 3.0 * f ** 1.35               # 2.4 -> ~5.4 mm/s (ISO zone C/D)
                    temp += 9.8 * f ** 1.2               # ~62 -> ~71.5 C
                    amp += 2.2 * f                        # load rises as the bearing binds
                    cool -= 0.6 * f                       # coolant slightly less effective
            if mid == "CNC-06":
                # Warning story: mild drift starting 5 days in, fully developed 4 days later.
                hours = (moment - READINGS_START).total_seconds() / 3600.0
                f = min(max(hours - 120.0, 0.0) / 96.0, 1.0)
                vib += 0.8 * f

            if status == "MAINTENANCE" and moment.date() == date(2026, 9, 28) and 8 <= hour < 12:
                rpm *= 0.55                               # PRS-03 warm-up under the PM window
                amp *= 0.60
            if status == "OFFLINE" and moment >= datetime(2026, 10, 1):
                rpm, amp, cool = 0.0, 0.0, 0.0            # PKG-04 idle: drifts toward ambient
                temp = 27.0 + diurnal + rng.gauss(0, 0.3)
                vib = 0.05 + abs(rng.gauss(0, 0.02))

            seq += 1
            rows.append([f"SR-{seq:06d}", mid, iso(moment), round(vib, 2), round(temp, 1),
                         round(rpm), round(amp, 1), round(max(cool, 0.0), 2), round(cycle, 1)])
            moment += step
    rows.sort(key=lambda r: (r[1], r[2]))
    for i, row in enumerate(rows, start=1):
        row[0] = f"SR-{i:06d}"

    # Scenario summary for the manifest (also the C2 sanity check in Snowflake).
    def window_mean(machine: str, col: int, start: datetime, end: datetime) -> float:
        vals = [float(r[col]) for r in rows if r[1] == machine and start <= parse_ts(r[2]) < end]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    scenario = {
        "machine": DEMO_MACHINE,
        "degradation_start": iso(DEGRADATION_START),
        "as_of": iso(AS_OF),
        "vibration_first24h_mean": window_mean(DEMO_MACHINE, 3, READINGS_START,
                                               READINGS_START + timedelta(days=1)),
        "vibration_last24h_mean": window_mean(DEMO_MACHINE, 3, AS_OF - timedelta(days=1), AS_OF),
        "temp_first24h_mean": window_mean(DEMO_MACHINE, 4, READINGS_START,
                                          READINGS_START + timedelta(days=1)),
        "temp_last24h_mean": window_mean(DEMO_MACHINE, 4, AS_OF - timedelta(days=1), AS_OF),
        "cadence": "10-minute for CNC-03, hourly for all other machines",
    }
    return header, rows, scenario


# --------------------------------------------------------------------------- spare_parts
# (part_id, name, category, compatible_machines, unit_cost_usd, stock, reorder, lead_days, supplier)
ALL_CNC = "CNC-01;CNC-02;CNC-03;CNC-04;CNC-05;CNC-06;CNC-07;CNC-08"
ALL_PRS = "PRS-01;PRS-02;PRS-03;PRS-04"
ALL_ASM = "ASM-01;ASM-02;ASM-03;ASM-04;ASM-05"
ALL_PKG = "PKG-01;PKG-02;PKG-03;PKG-04"
ALL_MACHINES = ";".join(m[0] for m in MACHINE_LAYOUT)

PART_SEEDS = [
    ("BRG-AX-17", "Axial spindle bearing 7014 CTYNDUL P4", "bearing", ALL_CNC,
     412.0, 2, 3, 7, "Gulf Bearing Trading LLC"),
    ("BRG-PR-04", "Press crankshaft roller bearing 23222", "bearing", ALL_PRS,
     890.0, 4, 2, 14, "Emirates Industrial Supplies"),
    ("BRG-PK-09", "Palletizer slewing ring bearing", "bearing", "PKG-02",
     2450.0, 1, 1, 30, "Gulf Bearing Trading LLC"),
    ("SPN-CN-02", "CNC spindle cartridge BT40 12000rpm", "spindle", ALL_CNC,
     6800.0, 1, 1, 45, "MachTech Gulf FZE"),
    ("HYD-AS-11", "Hydraulic seal kit 80mm bore", "seal_kit", ALL_PRS,
     240.0, 6, 3, 5, "Emirates Industrial Supplies"),
    ("FLT-CN-22", "CNC coolant filter cartridge 25um", "filter", ALL_CNC,
     58.0, 18, 8, 3, "FilterMart Middle East"),
    ("FLT-HY-07", "Hydraulic return filter 10um", "filter", ALL_PRS,
     74.0, 9, 4, 3, "FilterMart Middle East"),
    ("BLT-PK-05", "Conveyor V-belt SPZ 1250", "belt", "PKG-01;PKG-03",
     32.0, 12, 6, 4, "Gulf Belting Co."),
    ("BLT-AS-03", "Robot axis timing belt HTD-5M", "belt", ALL_ASM,
     46.0, 7, 4, 6, "Gulf Belting Co."),
    ("SEN-IR-09", "Infrared bearing temperature sensor", "sensor", ALL_CNC,
     189.0, 5, 2, 10, "Sensors & Systems Dubai"),
    ("SEN-VB-02", "Vibration sensor 100mV/g accelerometer", "sensor", ALL_MACHINES,
     215.0, 4, 2, 10, "Sensors & Systems Dubai"),
    ("ELT-CT-31", "Motor contactor 65A AC-3", "electrical", f"{ALL_PRS};{ALL_PKG}",
     96.0, 8, 3, 5, "Emirates Electrical Trading"),
    ("ELT-PS-12", "Servo drive power module 15kW", "electrical", ALL_ASM,
     1980.0, 1, 1, 21, "MachTech Gulf FZE"),
    ("LUB-GR-02", "High-speed spindle bearing grease (400g)", "lubricant", ALL_CNC,
     44.0, 14, 6, 4, "Gulf Lubricants LLC"),
    ("LUB-HY-05", "ISO VG46 hydraulic oil (20L)", "lubricant", ALL_PRS,
     78.0, 10, 4, 4, "Gulf Lubricants LLC"),
    ("COL-CN-08", "Semi-synthetic coolant concentrate (20L)", "lubricant", ALL_CNC,
     92.0, 8, 4, 5, "Gulf Lubricants LLC"),
    ("TOO-CN-14", "BT40 tool holder set (4pc)", "tooling", ALL_CNC,
     560.0, 3, 2, 12, "MachTech Gulf FZE"),
    ("GN-QLT-06", "CMM touch probe styli set (5pc)", "tooling", "QLT-01;QLT-03",
     320.0, 2, 1, 15, "Metrology Gulf"),
    ("LGT-PK-11", "Stretch wrapper carriage rollers", "wearer", "PKG-03",
     65.0, 6, 3, 8, "Emirates Industrial Supplies"),
    ("NOZ-CN-19", "Coolant spray nozzle kit", "wearer", ALL_CNC,
     28.0, 20, 10, 3, "Emirates Industrial Supplies"),
    ("BRG-AS-07", "Robot harmonic drive bearing CSF-25", "bearing", ALL_ASM,
     940.0, 2, 1, 18, "Gulf Bearing Trading LLC"),
    ("PMP-CN-11", "Coolant pump 1.5kW with V-bolt mount", "pump", ALL_CNC,
     430.0, 3, 2, 9, "Emirates Industrial Supplies"),
    ("MOT-CN-21", "Spindle drive motor 22kW", "motor", "CNC-05;CNC-06",
     5400.0, 1, 1, 35, "MachTech Gulf FZE"),
    ("VLV-HY-09", "Proportional hydraulic valve cartridge", "valve", ALL_PRS,
     760.0, 3, 2, 12, "Emirates Industrial Supplies"),
    ("SEN-PR-05", "Press pressure transducer 0-600bar", "sensor", ALL_PRS,
     310.0, 4, 2, 10, "Sensors & Systems Dubai"),
    ("SEN-PK-03", "Photoelectric label sensor", "sensor", ALL_PKG,
     145.0, 6, 3, 7, "Sensors & Systems Dubai"),
    ("FLT-PK-14", "Pneumatic air filter element 5um", "filter", ALL_PKG,
     26.0, 15, 8, 3, "FilterMart Middle East"),
    ("ELT-BR-08", "Servo brake resistor 120 ohm", "electrical", ALL_ASM,
     175.0, 4, 2, 10, "Emirates Electrical Trading"),
    ("CAB-AS-15", "Robot dress-pack cable set", "electrical", ALL_ASM,
     620.0, 2, 1, 20, "MachTech Gulf FZE"),
    ("CHN-PK-07", "Conveyor roller chain 08B x 3m", "wearer", "PKG-01;PKG-02",
     88.0, 5, 3, 6, "Gulf Belting Co."),
    ("GN-QLT-08", "Vision lens and lighting kit", "tooling", "QLT-02",
     540.0, 1, 1, 18, "Metrology Gulf"),
    ("GRS-PL-01", "Multipurpose EP2 grease (1kg)", "lubricant", ALL_MACHINES,
     22.0, 24, 12, 3, "Gulf Lubricants LLC"),
]


def build_spare_parts() -> tuple[list[str], list[list]]:
    header = ["part_id", "name", "category", "compatible_machines", "unit_cost_usd",
              "stock_qty", "reorder_point", "lead_time_days", "supplier"]
    return header, [list(p) for p in PART_SEEDS]


# ------------------------------------------------------------------- maintenance_history
FAILURE_MODES = {
    "CNC": ["bearing_wear", "spindle_drift", "heat_dissipation", "overstrain", "sensor_fault"],
    "PRESS": ["hydraulic_leak", "overstrain", "bearing_wear", "electrical_fault"],
    "ASSEMBLY": ["belt_slip", "servo_fault", "sensor_fault", "bearing_wear"],
    "PACKAGING": ["belt_slip", "electrical_fault", "bearing_wear", "sensor_fault"],
    "QUALITY": ["sensor_fault", "calibration_drift"],
}
TECHNICIANS = ["A. Rahman", "J. D'Souza", "M. Al-Farsi", "S. Kulkarni", "V. Menon", "H. Al-Mansoori"]

# Fixed historical CNC-03 bearing story: two prior bearing repairs, both consuming
# BRG-AX-17 - this is the evidence the Cortex Agent will cite in the demo.
CNC03_PRIOR_BEARING_EVENTS = [
    ("2025-12-14T10:20:00", "corrective", "bearing_wear",
     "Spindle front bearing replaced after vibration alarm (6.1 mm/s RMS) and 74 C bearing temperature.",
     "BRG-AX-17", 5.5),
    ("2026-05-02T08:05:00", "corrective", "bearing_wear",
     "Repeat spindle bearing replacement; grease analysis showed metal particles. "
     "Vibration back to 2.3 mm/s after swap.",
     "BRG-AX-17", 5.0),
]


def failure_mode_for(mid: str, mtype: str, rng: Random, is_corrective: bool) -> str:
    if not is_corrective:
        return "none"
    modes = [m for m in FAILURE_MODES[mtype] if not (mid == DEMO_MACHINE and m == "bearing_wear")]
    weights = [3, 2, 1, 1, 1][: len(modes)]
    return rng.choices(modes, weights=weights)[0]


def parts_for_mode(mode: str, mid: str) -> str:
    if mode == "bearing_wear":
        if mid.startswith("CNC"):
            return "BRG-AX-17"
        if mid == "PRS-01" or mid == "PRS-02" or mid == "PRS-03" or mid == "PRS-04":
            return "BRG-PR-04"
        if mid == "PKG-02":
            return "BRG-PK-09"
        return ""
    mapping = {
        "hydraulic_leak": "HYD-AS-11",
        "spindle_drift": "SPN-CN-02",
        "heat_dissipation": "COL-CN-08;FLT-CN-22",
        "belt_slip": ("CHN-PK-07" if mid == "PKG-02"
                      else "BLT-PK-05" if mid.startswith("PKG") else "BLT-AS-03"),
        "sensor_fault": "SEN-IR-09" if mid.startswith("CNC") else "SEN-VB-02",
        "servo_fault": "ELT-PS-12",
        "electrical_fault": "ELT-CT-31",
        "calibration_drift": "GN-QLT-06",
        "overstrain": "",
    }
    return mapping.get(mode, "")


def build_maintenance_history_and_work_orders() -> tuple[
    tuple[list[str], list[list]], tuple[list[str], list[list]], dict[tuple[str, date], int]
]:
    """History rows and the work orders they imply. Returns both tables plus a map of
    (machine, day) -> unplanned downtime minutes for the production/downtime tables."""
    hist_header = ["event_id", "machine_id", "event_ts", "event_type", "failure_mode",
                   "description", "technician", "duration_hours", "downtime_hours",
                   "parts_used", "work_order_id"]
    wo_header = ["work_order_id", "machine_id", "title", "type", "priority", "status",
                 "created_at", "scheduled_for", "completed_at", "assigned_to", "source",
                 "related_part_id", "description"]

    history: list[list] = []
    work_orders: list[list] = []
    downtime_by_machine_day: dict[tuple[str, date], int] = {}
    seq = 0
    wo_seq = 0

    def add_wo(machine: str, wtype: str, priority: str, status: str, created: datetime,
               scheduled: datetime, completed: datetime | None, tech: str, source: str,
               part: str, description: str) -> str:
        nonlocal wo_seq
        wo_seq += 1
        wid = f"WO-{wo_seq:04d}"
        work_orders.append([
            wid, machine, description.split(".")[0][:60] or f"{wtype.title()} work", wtype,
            priority, status, iso(created), iso(scheduled),
            iso(completed) if completed else "", tech, source, part, description,
        ])
        return wid

    for mid, _line, mtype, label, *_rest in MACHINE_LAYOUT:
        rng = make_rng(f"history:{mid}")
        n_events = rng.randint(5, 6)
        # Spread over the ~18 months before the readings window (Apr 2025 -> late Sep 2026,
        # so recent correctives land inside the 14-day production-runs window and reconcile).
        window_start = datetime(2025, 4, 1)
        stamps = sorted(
            window_start + timedelta(minutes=rng.randrange(0, 545 * 24 * 60)) for _ in range(n_events)
        )
        machine_downtime: dict[date, int] = {}

        for moment in stamps:
            # High-activity machines (CNCs, presses) get more correctives than the rest.
            # Rates are set so completed work orders land well inside the 50-100 target.
            is_corrective = rng.random() < (0.45 if mtype in ("CNC", "PRESS") else 0.30)
            is_preventive = not is_corrective and rng.random() < 0.30
            event_type = ("corrective" if is_corrective
                          else "preventive" if is_preventive
                          else "inspection" if rng.random() < 0.65 else "calibration")
            mode = failure_mode_for(mid, mtype, rng, is_corrective)
            duration = round(rng.uniform(0.8, 6.5), 1)
            downtime = round(duration * rng.uniform(0.4, 1.0), 1) if event_type == "corrective" else 0.0
            parts = parts_for_mode(mode, mid) if event_type in ("corrective", "preventive") else ""
            tech = pick(rng, TECHNICIANS)
            mode_txt = "" if mode == "none" else f" ({mode.replace('_', ' ')})"
            outcome = ("repair completed and function-tested" if event_type == "corrective"
                       else "completed per SOP checklist")
            desc = f"{event_type.title()} visit on {label} at {mid}{mode_txt}: {outcome}."

            if event_type in ("corrective", "preventive"):
                priority = ("high" if event_type == "corrective" and duration > 4
                            else "medium" if event_type == "corrective" else "low")
                wid = add_wo(mid, event_type, priority, "completed",
                             moment - timedelta(hours=2), moment, moment + timedelta(hours=duration),
                             tech, pick(rng, ["OPERATOR", "PLANNER"]),
                             parts.split(";")[0] if parts else "", desc)
            else:
                wid = ""

            if event_type == "corrective" and downtime > 0:
                machine_downtime[moment.date()] = machine_downtime.get(moment.date(), 0) + int(downtime * 60)

            seq += 1
            history.append([f"ME-{seq:03d}", mid, iso(moment), event_type, mode, desc,
                            tech, duration, downtime, parts, wid])

        # Inject the fixed CNC-03 bearing narrative (not random - always present).
        if mid == DEMO_MACHINE:
            for stamp, etype, mode, desc, part, dur in CNC03_PRIOR_BEARING_EVENTS:
                seq += 1
                moment = parse_ts(stamp)
                wid = add_wo(mid, etype, "high", "completed", moment - timedelta(hours=2), moment,
                             moment + timedelta(hours=dur), TECHNICIANS[2], "PLANNER", part, desc)
                history.append([f"ME-{seq:03d}", mid, stamp, etype, mode, desc,
                                TECHNICIANS[2], dur, round(dur * 0.8, 1), part, wid])

        for day, minutes in machine_downtime.items():
            downtime_by_machine_day[(mid, day)] = downtime_by_machine_day.get((mid, day), 0) + minutes

    history.sort(key=lambda r: r[2])
    for i, row in enumerate(history, start=1):
        row[0] = f"ME-{i:03d}"
    return (hist_header, history), (wo_header, work_orders), downtime_by_machine_day


# Candidates for the planner's scheduled calendar; consumed in order (deterministic) to
# top the work-order table up to its target size regardless of the random history draw.
SCHEDULED_POOL = [
    ("CNC-01", "Preventive spindle greasing", "preventive", "low", "LUB-GR-02", 2),
    ("CNC-05", "Quarterly alignment check", "inspection", "low", "", 2),
    ("CNC-08", "Tool magazine maintenance", "preventive", "low", "TOO-CN-14", 3),
    ("PRS-01", "Hydraulic oil replacement", "preventive", "medium", "LUB-HY-05", 4),
    ("PRS-04", "Press safety valve test", "inspection", "medium", "", 5),
    ("ASM-01", "Robot preventive calibration", "calibration", "low", "", 5),
    ("ASM-05", "Gripper wear replacement", "preventive", "low", "", 7),
    ("PKG-01", "Case packer belt replacement", "preventive", "low", "BLT-PK-05", 8),
    ("PKG-03", "Wrapper roller service", "preventive", "low", "LGT-PK-11", 9),
    ("QLT-01", "CMM annual verification", "calibration", "medium", "GN-QLT-06", 10),
    ("QLT-02", "Vision system light replacement", "preventive", "low", "", 11),
    ("CNC-02", "Coolant filter change", "preventive", "low", "FLT-CN-22", 12),
    ("CNC-06", "Vibration re-scan after drift", "inspection", "medium", "", 6),
    ("CNC-04", "Spindle drawbar force test", "inspection", "medium", "", 13),
]
WORK_ORDER_TARGET = 88  # final table size lands in [WORK_ORDER_TARGET, 100]


def append_future_work_orders(work_orders: list[list]) -> list[list]:
    """Add the in-progress / scheduled / proposed orders, including the demo-critical
    PROPOSED bearing replacement for CNC-03 on the least disruptive window."""
    rng = make_rng("workorders:future")
    tech = pick(rng, TECHNICIANS)

    def add(machine: str, title: str, wtype: str, priority: str, status: str,
            created: datetime, scheduled: datetime, source: str, part: str, desc: str) -> None:
        work_orders.append([f"WO-{len(work_orders) + 1:04d}", machine, title, wtype, priority,
                            status, iso(created), iso(scheduled), "", tech, source, part, desc])

    # In progress (3)
    add("PRS-03", "Quarterly hydraulic PM - press 3", "preventive", "medium", "in_progress",
        AS_OF - timedelta(days=2, hours=3), AS_OF - timedelta(days=1), "PLANNER", "HYD-AS-11",
        "Scheduled quarterly hydraulic maintenance: seal kit, oil change, filter replacement.")
    add("ASM-03", "Axis 2 timing belt replacement", "corrective", "high", "in_progress",
        AS_OF - timedelta(hours=9), AS_OF - timedelta(hours=6), "OPERATOR", "BLT-AS-03",
        "Belt slip detected during cycle audit; replacement in progress.")
    add("PKG-02", "Palletizer slew bearing inspection", "inspection", "medium", "in_progress",
        AS_OF - timedelta(hours=14), AS_OF - timedelta(hours=8), "PLANNER", "",
        "Inspect slewing ring after intermittent alarm; grease and re-torque.")
    # Scheduled upcoming: top up to the target size from the deterministic pool.
    n_scheduled = max(0, WORK_ORDER_TARGET - len(work_orders) - 2)  # minus the 2 proposed below
    for i in range(n_scheduled):
        machine, title, wtype, priority, part, days_ahead = SCHEDULED_POOL[i % len(SCHEDULED_POOL)]
        add(machine, title, wtype, priority, "scheduled",
            AS_OF - timedelta(days=1), AS_OF + timedelta(days=days_ahead, hours=6), "PLANNER", part,
            f"{title} - scheduled inside the planned maintenance calendar.")
    # Proposed by FACTORA_AGENT (2): the demo-critical CNC-03 bearing work order first.
    add(DEMO_MACHINE, "Replace spindle front bearing (BRG-AX-17)", "corrective", "critical", "proposed",
        AS_OF - timedelta(hours=3), AS_OF + timedelta(days=1, hours=7), "FACTORA_AGENT", "BRG-AX-17",
        "PROPOSED by Factora: bearing-failure risk predicted from a 5-day rising vibration "
        "(2.4 -> 5.3 mm/s RMS) and bearing temperature (62 -> 71 C); two prior bearing repairs on "
        "record (Dec 2025, May 2026). BRG-AX-17 in stock (2 of reorder point 3). Window: Sunday "
        "2026-10-04 07:00 - lowest production impact.")
    add("CNC-06", "Investigate rising vibration trend", "inspection", "high", "proposed",
        AS_OF - timedelta(hours=5), AS_OF + timedelta(days=2, hours=7), "FACTORA_AGENT", "SEN-VB-02",
        "PROPOSED by Factora: gradual vibration drift (+0.8 mm/s over 4 days) detected on CNC-06; "
        "inspection recommended before it escalates.")
    return work_orders


# ------------------------------------------------------------------------ production_runs
def build_small_stops() -> dict[tuple[str, date], int]:
    """Everyday minor stops (changeovers, material hiccups, small faults) over the
    production window. Keeps downtime_events inside its 50-100 target and fully
    reconcilable with production_runs.downtime_minutes."""
    stops: dict[tuple[str, date], int] = {}
    for mid, _line, _mtype, *_rest in MACHINE_LAYOUT:
        status = MACHINE_STATUS.get(mid, "HEALTHY")
        day = RUNS_START.date()
        while day <= AS_OF.date():
            if not (status == "OFFLINE" and day >= date(2026, 10, 1)):
                rng = make_rng(f"stop:{mid}:{day.isoformat()}")
                if rng.random() < 0.20:
                    stops[(mid, day)] = rng.randint(5, 40)
            day += timedelta(days=1)
    return stops


def build_production_runs(
    downtime_by_machine_day: dict[tuple[str, date], int]
) -> tuple[list[str], list[list]]:
    header = ["run_id", "machine_id", "run_date", "planned_output_units", "actual_output_units",
              "good_units", "ideal_cycle_time_s", "runtime_minutes", "planned_runtime_minutes",
              "downtime_minutes"]
    rows: list[list] = []
    seq = 0
    for mid, _line, _mtype, *_rest in MACHINE_LAYOUT:
        rng = make_rng(f"runs:{mid}")
        ideal = CYCLE_TIME_S[mid]
        status = MACHINE_STATUS.get(mid, "HEALTHY")
        day = RUNS_START.date()
        while day <= AS_OF.date():
            # GCC shift pattern: Mon-Thu one full shift, Fri half shift, Sat/Sun one shift.
            planned_minutes = 480 if day.weekday() < 4 else (240 if day.weekday() == 4 else 480)
            offline = (status == "OFFLINE" and day >= date(2026, 10, 1))
            if offline:
                # Out of service: not planned production time; the open downtime event row
                # carries the outage. Row kept with zeros for calendar continuity.
                planned_minutes = runtime = downtime_minutes = 0
            else:
                if mid == "PRS-03" and day == date(2026, 9, 28):
                    planned_minutes -= 240                      # planned PM window (DT row)
                downtime_minutes = min(downtime_by_machine_day.get((mid, day), 0), planned_minutes)
                runtime = planned_minutes - downtime_minutes
            perf = rng.uniform(0.86, 0.97)
            total = int(runtime * 60 / ideal * perf) if runtime else 0
            scrap_rate = rng.uniform(0.008, 0.03)
            if mid == DEMO_MACHINE and day >= (AS_OF - timedelta(days=3)).date():
                # Quality dip as the bearing degrades (chatter -> scrap), ramping up.
                scrap_rate += 0.02 * ((day - (AS_OF - timedelta(days=3)).date()).days + 1)
            good = int(total * (1 - min(scrap_rate, 0.15)))
            planned_output = int(planned_minutes * 60 / ideal)
            seq += 1
            rows.append([f"PR-{seq:04d}", mid, day.isoformat(), planned_output, total, good,
                         ideal, runtime, planned_minutes, downtime_minutes])
            day += timedelta(days=1)
    return header, rows


# ------------------------------------------------------------------------ downtime_events
def build_downtime_events(
    downtime_by_machine_day: dict[tuple[str, date], int]
) -> tuple[list[str], list[list]]:
    """Downtime rows for the 14-day production window (unplanned stops reconcile 1:1 with
    production_runs.downtime_minutes), plus the planned PM window and the open PKG-04
    outage. Earlier history-period downtime lives only in maintenance_history."""
    header = ["event_id", "machine_id", "start_ts", "end_ts", "duration_minutes",
              "cause_category", "description", "production_impact_units"]
    causes = ["mechanical_failure", "electrical_failure", "changeover", "material_shortage",
              "operator_error", "unknown"]
    rows: list[list] = []
    seq = 0
    window_days = [RUNS_START.date() + timedelta(days=i) for i in range(14)]
    in_window = {k: v for k, v in downtime_by_machine_day.items() if k[1] in window_days}
    for (mid, day), minutes in sorted(in_window.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        rng = make_rng(f"downtime:{mid}:{day.isoformat()}")
        start_hour = rng.randint(6, 18)
        start = datetime.combine(day, datetime.min.time()) + timedelta(hours=start_hour)
        # Cap the event inside the shift so end_ts stays same-day (simple, documented).
        duration = min(minutes, (23 - start_hour) * 60)
        end = start + timedelta(minutes=duration)
        cause = pick(rng, causes)
        impact = int(duration * 60 / CYCLE_TIME_S[mid])
        seq += 1
        rows.append([f"DT-{seq:03d}", mid, iso(start), iso(end), duration, cause,
                     f"Unplanned stop logged by the shift supervisor ({cause.replace('_', ' ')}).", impact])

    # Planned window and the open outage (end_ts empty = ongoing at as_of).
    planned = [
        ("PRS-03", "2026-09-28T08:00:00", "2026-09-28T12:00:00", "planned_maintenance",
         "Quarterly hydraulic PM window (work order in progress at snapshot).", 0),
        ("PKG-04", "2026-10-01T00:00:00", "", "electrical_failure",
         "OPEN EVENT: labeler drive fault; machine offline pending spare (end_ts empty = ongoing).", 0),
    ]
    for mid, start_s, end_s, cause, desc, _impact in planned:
        start = parse_ts(start_s)
        if end_s:
            duration = int((parse_ts(end_s) - start).total_seconds() // 60)
        else:
            duration = int((AS_OF - start).total_seconds() // 60)
        seq += 1
        rows.append([f"DT-{seq:03d}", mid, start_s, end_s, duration, cause, desc, 0])
    rows.sort(key=lambda r: r[2])
    for i, row in enumerate(rows, start=1):
        row[0] = f"DT-{i:03d}"
    return header, rows


# -------------------------------------------------------------------- maintenance_knowledge
# Hand-written corpus for Cortex Search (deterministic by construction: literal rows).
KNOWLEDGE_CHUNKS = [
    # CNC - bearing procedures (the demo evidence base; several cite BRG-AX-17)
    ("CNC", "procedure", "Spindle bearing replacement - removal and fit",
     "Isolate and lock out the machine. Release spindle drawbar tension and remove the tool holder and front "
     "cover. Support the spindle cartridge, remove the retaining ring and pull the front bearing assembly. "
     "Fit the new 7014 CTYNDUL P4 axial bearing (part BRG-AX-17) using an induction heater at 90 C; never "
     "hammer a precision bearing. Torque the retaining nut to 45 Nm in three stages.", "BRG-AX-17",
     "MA-CNC-SP-001"),
    ("CNC", "procedure", "Spindle bearing replacement - run-in and acceptance",
     "After bearing replacement (BRG-AX-17), run the spindle-in schedule: 10 min at 20% speed, 10 min at 40%, "
     "10 min at 60% with 5-minute cool-down gaps. Acceptance: housing temperature below 55 C and vibration "
     "below 2.8 mm/s RMS at 8000 rpm. Record final values in the CMMS before closing the work order.",
     "BRG-AX-17", "MA-CNC-SP-002"),
    ("CNC", "sop", "Spindle bearing failure symptoms and alarm limits",
     "Early symptoms of spindle bearing wear: rising vibration RMS (above 4.5 mm/s at speed), bearing housing "
     "temperature above 68 C at nominal load, increased motor current at constant feed, and a rough or gritty "
     "noise under rotation. Confirm with an envelope spectrum: bearing defect frequencies (BPFO/BPFI) indicate "
     "raceway damage. Replace the bearing (BRG-AX-17) before vibration exceeds ISO 10816 zone D.", "BRG-AX-17",
     "MA-CNC-SP-003"),
    ("CNC", "manual", "ISO 10816 vibration severity zones for machining centres",
     "Vibration RMS guidelines for spindles measured on the bearing housing: Zone A (good) below 2.8 mm/s; "
     "Zone B (acceptable) 2.8 to 4.5 mm/s; Zone C (unsatisfactory - plan maintenance) 4.5 to 7.1 mm/s; "
     "Zone D (danger - stop the machine) above 7.1 mm/s. Trend the weekly reading; a doubling of RMS within "
     "30 days is an early warning regardless of absolute zone.", "", "MA-CNC-VB-010"),
    ("CNC", "repair_note", "CNC-03 May 2026 bearing repair findings",
     "During the May 2026 repair of CNC-03, the removed front bearing showed brinelling on the outer race and "
     "grease with metallic particles. Root cause: grease interval exceeded by 6 weeks combined with coolant "
     "mist ingress. Corrective actions: shorten greasing interval to 400 spindle-hours and verify labyrinth "
     "seals at every quarterly PM. Part used: BRG-AX-17.", "BRG-AX-17", "RN-CNC-03-2026-05"),
    ("CNC", "sop", "Spindle greasing interval and grease quantity",
     "Grease spindle bearings (BRG-AX-17 fitted machines) every 400 spindle-hours or 8 weeks, whichever comes "
     "first. Quantity: 3.5 g per bearing using the specified high-speed spindle grease (LUB-GR-02). Over-"
     "greasing causes heat; log every top-up in the CMMS against the machine asset number.", "LUB-GR-02",
     "MA-CNC-LB-011"),
    ("CNC", "bulletin", "Bearing temperature alarm thresholds",
     "Factory bulletin: bearing temperature alarms for CNC machining centres are set at 65 C (warning) and "
     "72 C (critical). If temperature rises more than 5 C in 24 hours at constant load, inspect the bearing "
     "and coolant system the same shift. Do not silence the alarm without a recorded inspection.", "BRG-AX-17",
     "BU-CNC-TM-004"),
    ("CNC", "procedure", "Coolant system concentration and filter service",
     "Check coolant concentration daily with a refractometer; target 8 to 10 percent for aluminium, 6 to 8 "
     "percent for steel. Replace the 25 um filter cartridge (FLT-CN-22) when differential pressure exceeds "
     "1.8 bar or at every quarterly PM. Low coolant pressure below 5.5 bar at speed indicates pump wear or a "
     "blocked filter - both accelerate bearing wear.", "FLT-CN-22", "MA-CNC-CL-012"),
    # CNC - spindle/heat/overstrain
    ("CNC", "manual", "Spindle drift compensation and geometry check",
     "Thermal spindle drift beyond 12 um at the nose requires a geometry check: verify level and square of the "
     "headstock, re-run the ballbar test, and update the thermal compensation table. Persistent drift with "
     "normal temperatures indicates bearing preload loss - inspect the bearing pack (BRG-AX-17 machines).",
     "", "MA-CNC-GM-013"),
    ("CNC", "sop", "Heat dissipation failure mode (HDF) response",
     "An HDF-style failure is indicated when the air-to-process temperature difference falls below 8.6 K while "
     "rotational speed is below 1380 rpm. Response: verify cabinet and spindle cooling fans, clean heat "
     "exchangers, check coolant level and flow, and only then restart. Repeated HDF events justify a cooling "
     "system overhaul before the next production campaign.", "", "MA-CNC-HT-014"),
    ("CNC", "repair_note", "Overstrain failure on CNC-05 (case note)",
     "CNC-05 tripped on overstrain after an operator ran a dull tool at high feed: torque and tool wear "
     "product exceeded the machine limit. Action: tool life management rules updated; feed overrides now "
     "logged. No bearing damage found; vibration normal after tool change.", "", "RN-CNC-05-2026-02"),
    ("CNC", "sop", "Tool wear limits by material",
     "Replace milling tools at 200 to 240 minutes of cumulative wear (H variant 5 min added, M 3 min, L 2 min "
     "per tool change). Running past the wear limit raises torque and bearing load and is the leading cause "
     "of overstrain trips on the CNC line. The CMMS blocks auto-release of tools past the wear limit.",
     "", "MA-CNC-TL-015"),
    ("CNC", "manual", "Motor current as a bearing health indicator",
     "Track motor current at a repeatable cycle. A bearing under mechanical stress raises current 5 to 10 "
     "percent at constant feed before vibration alarms trigger. Investigate any sustained current rise above "
     "10 percent from the 30-day baseline: check belt tension, tool condition, then the spindle bearing.",
     "", "MA-CNC-EL-016"),
    # Press
    ("PRESS", "procedure", "Hydraulic press quarterly PM checklist",
     "Quarterly press PM: replace hydraulic return filter (FLT-HY-07), sample oil for particle count, inspect "
     "hoses for abrasion, test relief valve at 110 percent of set pressure, verify ram alignment and gibs, "
     "and grease the crankshaft bearings (BRG-PR-04 machines). Record oil temperature at full stroke; above "
     "55 C indicates cooler fouling.", "FLT-HY-07", "MA-PRS-PM-020"),
    ("PRESS", "sop", "Hydraulic leak response",
     "On any hydraulic leak: stop the press, de-pressurise, place drip containment, and fit the 80 mm seal kit "
     "(HYD-AS-11) if the leak is from the ram gland. Never run a press below minimum tank level - pump "
     "cavitation destroys the pump and overheats the circuit. Log the leak location for the trend.",
     "HYD-AS-11", "MA-PRS-HY-021"),
    ("PRESS", "manual", "Press overstrain protection",
     "The press control stops the stroke when force exceeds 110 percent of the job setpoint. Repeated "
     "overstrain trips indicate double blanking, wrong material gauge or die wear. Reset only after physical "
     "inspection. Overstrain events above 3 per month require a die maintenance review.", "", "MA-PRS-OS-022"),
    ("PRESS", "repair_note", "PRS-02 crankshaft bearing replacement",
     "Replaced the crankshaft roller bearing (BRG-PR-04) after a 6.8 mm/s RMS vibration finding. The inner "
     "race showed spalling at the load zone. New bearing fitted with 0.02 mm shaft interference, heated to "
     "110 C. Post-repair vibration 1.9 mm/s. Grease interval extended records attached.", "BRG-PR-04",
     "RN-PRS-02-2026-01"),
    ("PRESS", "bulletin", "Press hydraulic oil specification",
     "Use ISO VG46 hydraulic oil (LUB-HY-05) exclusively. Mixing brands causes additive drop-out and filter "
     "blinding. Target cleanliness ISO 4406 18/16/13; sample quarterly. Water content above 200 ppm requires "
     "oil change and cooler leak test.", "LUB-HY-05", "BU-PRS-OI-023"),
    ("PRESS", "sop", "Press lockout-tagout",
     "Before any press intervention: energy isolation at the main disconnect, release accumulators to zero on "
     "the gauge, apply personal locks, and verify by attempting a start. Two-person rule applies for work "
     "under the ram. Failure to follow LOTO is a stop-work violation.", "", "MA-PRS-SF-024"),
    # Assembly
    ("ASSEMBLY", "procedure", "Robot axis timing belt replacement",
     "For belt-slip alarms on axis 2 or 3: jog the axis to the service position, release the belt tensioner, "
     "replace the HTD-5M timing belt (BLT-AS-03), re-tension to the manufacturer mark, and re-run the axis "
     "zero master. Verify repeatability with a dial indicator: below 0.05 mm over 20 cycles.", "BLT-AS-03",
     "MA-ASM-BL-030"),
    ("ASSEMBLY", "sop", "Robot servo fault triage",
     "Servo faults on assembly robots: check the drive error code, inspect the encoder cable for chafing at "
     "the dress pack, and measure motor current at the faulted axis. A power module swap (ELT-PS-12) is the "
     "last step after cables and brakes are excluded. Reset the fault history after the repair.", "ELT-PS-12",
     "MA-ASM-SV-031"),
    ("ASSEMBLY", "manual", "Robot repeatability audit",
     "Monthly repeatability audit: run the 20-point circle program, record worst-point deviation. Alarm limit "
     "0.1 mm; investigate backlash, belt tension and mounting bolts if exceeded. Rising deviation with "
     "normal belts points to harmonic drive wear - schedule the gearbox inspection.", "", "MA-ASM-RA-032"),
    ("ASSEMBLY", "repair_note", "ASM-03 axis 2 belt slip (open item)",
     "ASM-03 reported intermittent axis 2 belt slip during heavy cycles. Belt replaced (BLT-AS-03); tensioner "
     "mark verified. Watching for recurrence: two more events within 30 days would justify tensioner "
     "replacement and encoder cable inspection.", "BLT-AS-03", "RN-ASM-03-2026-09"),
    ("ASSEMBLY", "sop", "Gripper maintenance and wear parts",
     "Inspect gripper fingers weekly for wear flats; replace pads at 0.5 mm wear. Misalignment from worn pads "
     "causes dropped parts and robot stops that look like servo faults. Keep one spare finger set per cell in "
     "the line-side bin.", "", "MA-ASM-GR-033"),
    ("ASSEMBLY", "bulletin", "Robot dress-pack cable care",
     "Bulletin: encoder and power cables fail at the dress pack first. Inspect for outer jacket wear at every "
     "PM; a chafed encoder cable produces intermittent servo faults that mimic drive failures. Replace the "
     "dress pack at 3 years regardless of appearance.", "", "BU-ASM-CB-034"),
    # Packaging
    ("PACKAGING", "procedure", "Palletizer slewing bearing inspection",
     "Inspect the palletizer slewing ring (BRG-PK-09) quarterly: rotate manually and feel for stepping, check "
     "grease condition, measure axial play (limit 0.8 mm). Play above limit or rough rotation requires the "
     "bearing to be scheduled for replacement - lead time is 30 days, so plan ahead.", "BRG-PK-09",
     "MA-PKG-SB-040"),
    ("PACKAGING", "sop", "Conveyor belt tracking and replacement",
     "Track belts with the machine running at low speed; adjust the snub rollers in quarter turns. Replace "
     "SPZ V-belts (BLT-PK-05) when cracks appear on the underside or when slippage exceeds 5 percent of rated "
     "tension. Always replace belts in full sets per conveyor.", "BLT-PK-05", "MA-PKG-BL-041"),
    ("PACKAGING", "repair_note", "PKG-04 labeler drive fault (open)",
     "PKG-04 labeler stopped with a drive overcurrent fault on 2026-10-01. Initial inspection found insulation "
     "damage on the drive motor. Machine left OFFLINE pending motor spare; work order to be raised. Production "
     "moved to the backup carton line meanwhile.", "", "RN-PKG-04-2026-10"),
    ("PACKAGING", "manual", "Labeler registration troubleshooting",
     "Misregistered labels: verify sensor gain against label backing, check the product divider timing, and "
     "inspect the applicator pad vacuum. Registration drift with clean sensors indicates encoder wheel wear "
     "on the product chain.", "", "MA-PKG-LB-042"),
    ("PACKAGING", "sop", "Stretch wrapper carriage service",
     "Service the stretch wrapper carriage every 6 months: replace carriage rollers (LGT-PK-11) in pairs, "
     "grease the mast chain, and verify film pre-stretch percentage (target 250 percent plus or minus 20).",
     "LGT-PK-11", "MA-PKG-WR-043"),
    ("PACKAGING", "bulletin", "Carton line backup plan",
     "When PKG-04 (labeler) is down, run pre-labelled cartons through the backup carton line at 60 percent "
     "rate. The backup line has no print-and-apply capability; labels are applied off-line. Notify planning "
     "so shift output targets are adjusted.", "", "BU-PKG-OP-044"),
    # Quality
    ("QUALITY", "procedure", "CMM annual verification",
     "Annual CMM verification (QLT-01, QLT-03): run the ball bar and gauge block tests, verify stylus tips "
     "(GN-QLT-06 set), compensate for temperature (target 20 C plus or minus 0.5), and file the certificate. "
     "A failed length test requires a manufacturer calibration visit before parts release continues.",
     "GN-QLT-06", "MA-QLT-CM-050"),
    ("QUALITY", "sop", "Vision system false reject response",
     "Rising false rejects on the vision station: clean the dome and ring lights, verify part presentation "
     "fixtures, and re-teach the golden sample. If false rejects persist after re-teach, replace the lighting "
     "unit before suspecting the camera.", "", "MA-QLT-VS-051"),
    ("QUALITY", "manual", "CMM probe styli handling",
     "Handle CMM styli (GN-QLT-06) with gloves; skin oils degrade ruby seating. Verify each stylus after "
     "crash or doubt using the reference sphere; reject any stylus with a damaged ruby. Broken styli cause "
     "silent measurement drift.", "GN-QLT-06", "MA-QLT-PR-052"),
    ("QUALITY", "sop", "Calibration drift escalation",
     "When a gauge or station shows calibration drift beyond half the product tolerance, quarantine the "
     "measurements since the last good verification and escalate to quality engineering the same day. "
     "Never adjust calibration factors without a recorded verification afterwards.", "", "MA-QLT-CD-053"),
    ("QUALITY", "bulletin", "Quality dip review trigger",
     "A rising scrap rate on any line (more than 1.5 percentage points above its 30-day baseline) triggers a "
     "quality review within 24 hours. For CNC machines, first check tool wear compliance, then spindle "
     "condition - bearing wear shows up as surface finish chatter before vibration alarms.", "", "BU-QLT-QR-054"),
    # Plant-wide
    ("ALL", "sop", "Work order lifecycle in the CMMS",
     "Work orders move through PROPOSED (created by the reliability agent or planner), SCHEDULED (assigned a "
     "window), IN_PROGRESS (technician started), COMPLETED (parts and time booked). Only PROPOSED and "
     "SCHEDULED orders can be cancelled. Every completed order requires failure mode and parts used recorded.",
     "", "MA-PLT-WO-060"),
    ("ALL", "sop", "Spare parts reorder policy",
     "Reorder when stock reaches the reorder point: raise a purchase request the same day citing lead time. "
     "Critical spares (bearings, servo modules) keep safety stock at the reorder point; running a critical "
     "spare below its reorder point requires the maintenance manager's sign-off and a mitigation note.",
     "", "MA-PLT-SR-061"),
    ("ALL", "sop", "Lockout-tagout (LOTO) plant standard",
     "All maintenance under LOTO: identify every energy source (electrical, hydraulic, pneumatic, gravity), "
     "isolate, dissipate stored energy, lock and tag, then verify zero energy by attempted start. One lock "
     "per person. Group lockboxes for multi-trade jobs.", "", "MA-PLT-SF-062"),
    ("ALL", "procedure", "Vibration monitoring program",
     "Route-based vibration readings are taken weekly on CNC and press assets (monthly on others) with a "
     "portable analyser: velocity RMS 10-1000 Hz on the bearing housing, plus envelope spectrum for rolling "
     "element bearings. Trends go into the CMMS; the reliability agent reads the same history.", "", "MA-PLT-VM-063"),
    ("ALL", "sop", "Oil analysis sampling",
     "Quarterly oil samples from presses and gearboxes: particle count, water content, viscosity and "
     "spectrometry. Iron above 150 ppm or copper above 50 ppm triggers a wear-metal investigation. Sample "
     "from the return line mid-stream while the machine runs.", "", "MA-PLT-OA-064"),
    ("ALL", "bulletin", "Preventive maintenance calendar policy",
     "The PM calendar is protected: planned maintenance windows are scheduled on weekend shifts first "
     "(lowest production impact), then shift overlaps. Friday runs a half shift, Saturday and Sunday one "
     "shift each. Moving a PM window requires the planner's approval 48 hours in advance.", "", "BU-PLT-PM-065"),
    ("ALL", "sop", "Machine status definitions",
     "Machine status vocabulary used across the plant systems: HEALTHY (running within limits), WARNING "
     "(degradation trend detected, increase monitoring), CRITICAL (failure likely, plan intervention), "
     "MAINTENANCE (under planned maintenance), OFFLINE (out of service, not producing). The digital twin and "
     "dashboards use the same vocabulary and colours.", "", "MA-PLT-ST-066"),
    ("ALL", "manual", "Failure mode catalogue - rolling element bearings",
     "Bearing failure stages: 1) ultrasonic noise only; 2) audible noise, temperature rise begins; 3) "
     "vibration RMS climb with defect frequencies in the envelope spectrum; 4) temperature sharply up, RMS "
     "above zone C; 5) imminent seizure. Plan replacement at stage 3; never run to stage 5 on a bottleneck "
     "asset. Fitted part on CNC spindles: BRG-AX-17.", "BRG-AX-17", "MA-PLT-FM-067"),
    ("ALL", "sop", "Parts consumption recording",
     "Book every part consumed against the work order before closing it. Unbooked parts break the inventory "
     "accuracy that the spare-parts planner depends on. Negative stock in the system is a data incident: "
     "report it the same day.", "", "MA-PLT-IN-068"),
    ("ALL", "bulletin", "Reliability agent usage guidelines",
     "The Factora reliability agent separates observed data, model predictions and recommendations, and cites "
     "its sources (telemetry trends, maintenance history, knowledge base). Treat its output as decision "
     "support: verify critical evidence in the source systems before committing downtime.", "", "BU-PLT-AG-069"),
    ("ALL", "sop", "Shift handover for degrading assets",
     "When a machine is on WARNING or CRITICAL, the outgoing supervisor records trend values, alarms and any "
     "temporary mitigations in the handover log, and the incoming supervisor acknowledges. Degrading assets "
     "are walked down in person at handover.", "", "MA-PLT-HO-070"),
    ("ALL", "procedure", "Bearing storage and handling",
     "Precision bearings are stored in their original sealed packaging, flat, in the dry-goods store. Before "
     "fitting: check the corrosion-inhibitor film, rotate by hand for smoothness, and never wash off the "
     "factory preservative unless specified. Damaged packaging = quarantine and inspect before use.",
     "BRG-AX-17", "MA-PLT-BS-071"),
    ("ALL", "manual", "OEE definitions used by this plant",
     "OEE = Availability x Performance x Quality. Availability = run time / planned production time. "
     "Performance = (ideal cycle time x total count) / run time. Quality = good count / total count. Planned "
     "maintenance windows reduce planned production time only when scheduled in advance; breakdowns always "
     "reduce run time.", "", "MA-PLT-OE-072"),
]


def build_knowledge() -> tuple[list[str], list[list]]:
    header = ["chunk_id", "machine_type", "document_type", "title", "content", "related_part_id", "source_document"]
    return header, [[f"KC-{i:03d}", *chunk] for i, chunk in enumerate(KNOWLEDGE_CHUNKS, start=1)]


# ----------------------------------------------------------------------------- validation
def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


# Per-table row-count windows (playbook data plan, PROJECT_SPEC.md section 7).
ROW_RANGES = {
    "machines": (24, 24),
    "sensor_readings": (10_000, 50_000),
    "maintenance_history": (100, 200),
    "spare_parts": (30, 50),
    "work_orders": (50, 100),
    "production_runs": (336, 336),      # 24 machines x 14 days
    "downtime_events": (50, 100),
    "maintenance_knowledge": (30, 80),
}


def validate_output(out_dir: Path, generated: dict[str, dict] | None = None) -> list[str]:
    """Consistency checks over the generated CSVs. `generated` maps name -> {header, rows}
    in memory; when None the files are read from `out_dir` (--verify path)."""
    tables: dict[str, tuple[list[str], list[dict]]] = {}

    def load(name: str) -> tuple[list[str], list[dict]]:
        if name in tables:
            return tables[name]
        if generated is not None and name in generated:
            header, rows = generated[name]["header"], generated[name]["rows"]
        else:
            with (out_dir / f"{name}.csv").open(newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
                rows = [dict(zip(header, r, strict=True)) for r in reader]
        tables[name] = (header, rows)
        return tables[name]

    errors: list[str] = []
    for name, (low, high) in ROW_RANGES.items():
        n = len(load(name)[1])
        require(low <= n <= high, f"{name}.csv has {n} rows, expected {low}-{high}", errors)

    machines = load("machines")[1]
    machine_ids = {m["machine_id"] for m in machines}
    states = {m["status"] for m in machines}
    require(states <= set(MACHINE_STATES), f"unknown machine states: {sorted(states - set(MACHINE_STATES))}", errors)
    for m in machines:
        for coord in ("x_m", "y_m", "z_m"):
            require(m[coord] != "", f"{m['machine_id']} missing twin coordinate {coord}", errors)
        if m["status"] == "OFFLINE":
            require(m["health_score"] == "", f"{m['machine_id']} offline must have empty health_score", errors)
        else:
            require(m["health_score"].isdigit(), f"{m['machine_id']} needs an integer health_score", errors)

    parts = load("spare_parts")[1]
    part_ids = {p["part_id"] for p in parts}
    part_compat = {p["part_id"]: set(p["compatible_machines"].split(";")) for p in parts}
    brg = next((p for p in parts if p["part_id"] == "BRG-AX-17"), None)
    require(brg is not None, "BRG-AX-17 missing from spare_parts", errors)
    if brg:
        require(DEMO_MACHINE in brg["compatible_machines"].split(";"),
                "BRG-AX-17 is not compatible with CNC-03", errors)
        require(int(brg["stock_qty"]) <= int(brg["reorder_point"]),
                "BRG-AX-17 stock is not limited (stock must be at or below reorder point)", errors)

    readings = load("sensor_readings")[1]
    # CNC-03 degradation scenario present and unambiguous.
    cnc03 = [r for r in readings if r["machine_id"] == DEMO_MACHINE]
    require(len(cnc03) >= 1_900, f"CNC-03 has only {len(cnc03)} readings (10-min cadence expected)", errors)

    def window_mean(rows: list[dict], col: str, start: datetime, end: datetime) -> float:
        vals = [float(r[col]) for r in rows if start <= parse_ts(r["ts"]) < end]
        return sum(vals) / len(vals) if vals else 0.0

    v_first = window_mean(cnc03, "vibration_rms_mm_s", READINGS_START, READINGS_START + timedelta(days=1))
    v_last = window_mean(cnc03, "vibration_rms_mm_s", AS_OF - timedelta(days=1), AS_OF)
    t_first = window_mean(cnc03, "bearing_temp_c", READINGS_START, READINGS_START + timedelta(days=1))
    t_last = window_mean(cnc03, "bearing_temp_c", AS_OF - timedelta(days=1), AS_OF)
    require(v_last > v_first * 1.8, f"CNC-03 vibration did not rise enough ({v_first:.2f} -> {v_last:.2f})", errors)
    require(t_last - t_first > 6.0, f"CNC-03 temperature did not rise enough ({t_first:.1f} -> {t_last:.1f})", errors)
    cnc03_machine = next(m for m in machines if m["machine_id"] == DEMO_MACHINE)
    require(cnc03_machine["status"] == "CRITICAL", "CNC-03 snapshot status is not CRITICAL", errors)

    for table, id_col in (("maintenance_history", "machine_id"), ("work_orders", "machine_id"),
                          ("production_runs", "machine_id"), ("downtime_events", "machine_id")):
        rows = load(table)[1]
        bad = {r[id_col] for r in rows} - machine_ids
        require(not bad, f"{table} references unknown machines: {sorted(bad)}", errors)

    work_orders = load("work_orders")[1]
    bad_parts = {r["related_part_id"] for r in work_orders if r["related_part_id"]} - part_ids
    require(not bad_parts, f"work_orders reference unknown parts: {sorted(bad_parts)}", errors)
    for r in work_orders:
        p = r["related_part_id"]
        require(not p or r["machine_id"] in part_compat[p],
                f"work order {r['work_order_id']} uses part {p} not compatible with {r['machine_id']}", errors)
    proposed = [r for r in work_orders if r["status"] == "proposed" and r["machine_id"] == DEMO_MACHINE
                and r["related_part_id"] == "BRG-AX-17"]
    require(len(proposed) == 1, "expected exactly one PROPOSED CNC-03 work order citing BRG-AX-17", errors)

    history = load("maintenance_history")[1]
    all_parts: set[str] = set()
    for r in history:
        all_parts |= {p for p in r["parts_used"].split(";") if p}
    unknown_parts = sorted(all_parts - part_ids)
    require(all_parts <= part_ids, f"maintenance_history references unknown parts: {unknown_parts}", errors)
    for r in history:
        for p in (x for x in r["parts_used"].split(";") if x):
            require(r["machine_id"] in part_compat[p],
                    f"history event {r['event_id']} uses part {p} not compatible with {r['machine_id']}", errors)
    cnc03_bearing_events = [r for r in history
                            if r["machine_id"] == DEMO_MACHINE and r["failure_mode"] == "bearing_wear"]
    require(len(cnc03_bearing_events) >= 2, "CNC-03 lacks prior bearing_wear history for the evidence story", errors)

    # Completed work orders pair 1:1 with the history rows that link to them.
    wo_ids = {w["work_order_id"] for w in work_orders}
    linked = [r["work_order_id"] for r in history if r["work_order_id"]]
    require(len(linked) == len(set(linked)), "maintenance_history links duplicate work orders", errors)
    require(set(linked) <= wo_ids, "maintenance_history links unknown work orders", errors)
    completed = {w["work_order_id"] for w in work_orders if w["status"] == "completed"}
    require(set(linked) == completed, "completed work orders and history links disagree", errors)

    # Unplanned (closed) downtime reconciles with production_runs.downtime_minutes.
    runs = load("production_runs")[1]
    runs_map = {(r["machine_id"], r["run_date"]):
                (int(r["downtime_minutes"]), int(r["planned_runtime_minutes"])) for r in runs}
    unplanned: dict[tuple[str, str], int] = {}
    for r in load("downtime_events")[1]:
        if r["cause_category"] != "planned_maintenance" and r["end_ts"] != "":
            key = (r["machine_id"], r["start_ts"][:10])
            unplanned[key] = unplanned.get(key, 0) + int(r["duration_minutes"])
    for (mid, day), minutes in unplanned.items():
        require((mid, day) in runs_map, f"downtime event on {mid} {day} has no production run row", errors)
        if (mid, day) in runs_map:
            recorded, planned = runs_map[(mid, day)]
            floor = min(minutes, planned)
            require(recorded >= floor,
                    f"downtime minutes for {mid} {day} under-record the event ({recorded} < {floor})", errors)
    for r in runs:
        require(int(r["runtime_minutes"]) == int(r["planned_runtime_minutes"]) - int(r["downtime_minutes"]),
                f"run {r['run_id']}: runtime != planned - downtime", errors)

    knowledge = load("maintenance_knowledge")[1]
    require(len({k["chunk_id"] for k in knowledge}) == len(knowledge), "duplicate knowledge chunk ids", errors)
    bad_types = {k["machine_type"] for k in knowledge} - (set(BASELINES) | {"ALL"})
    require(not bad_types, f"knowledge chunks reference unknown machine types: {sorted(bad_types)}", errors)
    bad_kparts = {k["related_part_id"] for k in knowledge if k["related_part_id"]} - part_ids
    require(not bad_kparts, f"maintenance_knowledge references unknown parts: {sorted(bad_kparts)}", errors)

    # Required (non-nullable) cells: every column except the documented optional ones.
    optional = {"parts_used", "related_part_id", "work_order_id", "completed_at",
                "health_score", "end_ts"}
    for name in ROW_RANGES:
        header, rows = load(name)
        for col in header:
            if col in optional:
                continue
            offenders = sum(1 for r in rows if r[col].strip() == "")
            require(offenders == 0, f"{name}.csv has {offenders} empty cells in required column {col}", errors)
    return errors


# ------------------------------------------------------------------------------------ main
def generate(out_dir: Path) -> tuple[dict[str, dict], dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables: dict[str, tuple[list[str], list[list]]] = {}
    tables["machines"] = build_machines()
    tables["spare_parts"] = build_spare_parts()
    readings_header, readings_rows, scenario = build_sensor_readings()
    tables["sensor_readings"] = (readings_header, readings_rows)
    hist, wos, downtime_map = build_maintenance_history_and_work_orders()
    for key, minutes in build_small_stops().items():
        downtime_map[key] = downtime_map.get(key, 0) + minutes
    wos = (wos[0], append_future_work_orders(list(wos[1])))
    tables["maintenance_history"], tables["work_orders"] = hist, wos
    tables["production_runs"] = build_production_runs(downtime_map)
    tables["downtime_events"] = build_downtime_events(downtime_map)
    tables["maintenance_knowledge"] = build_knowledge()

    summary: dict[str, dict] = {}
    for name, (header, rows) in tables.items():
        path = out_dir / f"{name}.csv"
        nrows = write_csv(path, header, rows)
        summary[name] = {"rows": nrows, "sha256": sha256_of(path), "bytes": path.stat().st_size}

    manifest = {
        "dataset": "factora-synthetic-factory",
        "generator": "scripts/generate_factory_data.py",
        "generator_sha256": sha256_of(GENERATOR_PATH),
        "seed": SEED,
        "as_of": iso(AS_OF),
        "note": ("All tables are synthetic (see data/README.md). The only real dataset is "
                 "data/raw/ai4i2020.csv (UCI AI4I 2020, CC BY 4.0), used by the F3 model."),
        "files": summary,
        "cnc03_scenario": scenario,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    generated = {name: {"header": h, "rows": [dict(zip(h, (str(c) for c in r), strict=True)) for r in rows]}
                 for name, (h, rows) in tables.items()}
    return generated, manifest


def print_summary(manifest: dict, out_dir: Path) -> None:
    print(f"Generated dataset in {out_dir}  (seed {manifest['seed']}, as_of {manifest['as_of']})")
    for name, info in manifest["files"].items():
        print(f"  {name + '.csv':26} {info['rows']:>6,} rows  {info['bytes']:>9,} bytes")
    s = manifest["cnc03_scenario"]
    print(f"  CNC-03 scenario: vibration {s['vibration_first24h_mean']} -> {s['vibration_last24h_mean']} mm/s, "
          f"bearing temp {s['temp_first24h_mean']} -> {s['temp_last24h_mean']} C "
          f"(first 24h -> last 24h of the window)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", action="store_true",
                        help="regenerate into a temp dir and byte-compare with data/generated")
    args = parser.parse_args()

    if args.verify:
        if not OUT_DIR.exists():
            print(f"{OUT_DIR} does not exist - run the generator first, then --verify", file=sys.stderr)
            return 1
        with tempfile.TemporaryDirectory(prefix="factora-verify-") as tmp:
            temp_dir = Path(tmp) / "generated"
            generate(temp_dir)
            existing = {p.name for p in OUT_DIR.iterdir()}
            fresh = {p.name for p in temp_dir.iterdir()}
            mismatches = [n for n in sorted(existing | fresh)
                          if not (temp_dir / n).exists()
                          or not (OUT_DIR / n).exists()
                          or sha256_of(OUT_DIR / n) != sha256_of(temp_dir / n)]
            if mismatches:
                print("DETERMINISM CHECK FAILED - files differ between runs:", file=sys.stderr)
                for name in mismatches:
                    print(f"  - {name}", file=sys.stderr)
                return 1
        print(f"DETERMINISM OK - re-run with seed {SEED} reproduced data/generated byte-identically "
              f"({len(existing)} files)")
        errors = validate_output(OUT_DIR)
        if errors:
            print("\nCONSISTENCY CHECK FAILED:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print("CONSISTENCY OK - all tables non-empty, cross-references and the CNC-03 scenario verified")
        return 0

    generated, manifest = generate(OUT_DIR)
    print_summary(manifest, OUT_DIR)
    errors = validate_output(OUT_DIR, generated=generated)
    if errors:
        print("\nCONSISTENCY CHECK FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("CONSISTENCY OK - all tables non-empty, cross-references and the CNC-03 scenario verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
