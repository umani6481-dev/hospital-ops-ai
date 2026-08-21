"""
Synthetic Hospital Operations Dataset Generator
=================================================
Generates realistic (but 100% SYNTHETIC / DEMO) operational data for the
Hospital Operations AI platform: patients, visits, appointments, and
hospital events across multiple departments and 12+ months of history.

NOTE: This data is entirely artificial and must never be treated as, or
presented as, real patient data.

Usage:
    python -m scripts.generate_dataset --days 400 --out ml/data/raw
"""
import argparse
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
random.seed(42)
np.random.seed(42)

DEPARTMENTS = [
    {"name": "Emergency", "capacity": 100, "base_demand": 60},
    {"name": "OPD - General Medicine", "capacity": 150, "base_demand": 120},
    {"name": "Cardiology", "capacity": 60, "base_demand": 40},
    {"name": "Orthopedics", "capacity": 50, "base_demand": 30},
    {"name": "Pediatrics", "capacity": 70, "base_demand": 45},
    {"name": "Radiology", "capacity": 40, "base_demand": 25},
]

VISIT_TYPES = ["OPD", "Emergency", "Follow-up", "Appointment", "Walk-in"]
AGE_GROUPS = ["0-12", "13-18", "19-35", "36-55", "56-70", "70+"]
GENDERS = ["Male", "Female", "Other"]
REGIONS = ["North", "South", "East", "West", "Central"]

EVENT_POOL = [
    ("Staff Shortage", "high"), ("Equipment Unavailable", "medium"),
    ("Emergency Surge", "critical"), ("Public Holiday", "medium"),
    ("Weather Event", "high"), ("System Outage", "low"),
]


def seasonal_factor(date: datetime) -> float:
    # Winter months (flu season) => higher demand
    month = date.month
    if month in (12, 1, 2):
        return 1.25
    if month in (6, 7, 8):
        return 0.9
    return 1.0


def weekday_factor(date: datetime) -> float:
    wd = date.weekday()  # Monday=0
    if wd == 0:
        return 1.2  # Monday surge
    if wd in (5, 6):
        return 0.75  # weekend dip
    return 1.0


def generate(days: int, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    start_date = datetime.utcnow() - timedelta(days=days)

    visits_rows = []
    appointments_rows = []
    events_rows = []
    daily_dept_rows = []

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        s_factor = seasonal_factor(current_date)
        w_factor = weekday_factor(current_date)

        # Randomly inject an operational event some days
        active_event = None
        if random.random() < 0.06:
            title, severity = random.choice(EVENT_POOL)
            dept_choice = random.choice(DEPARTMENTS)["name"]
            events_rows.append({
                "event_date": current_date.date().isoformat(),
                "title": title,
                "department": dept_choice,
                "severity": severity,
            })
            active_event = {"department": dept_choice, "severity": severity}

        for dept in DEPARTMENTS:
            noise = np.random.normal(1.0, 0.12)
            event_boost = 1.0
            if active_event and active_event["department"] == dept["name"]:
                boost_map = {"low": 1.05, "medium": 1.15, "high": 1.3, "critical": 1.5}
                event_boost = boost_map.get(active_event["severity"], 1.0)

            expected_patients = dept["base_demand"] * s_factor * w_factor * noise * event_boost
            expected_patients = max(0, int(round(expected_patients)))

            # Hourly distribution (peak in afternoon for OPD, all-day for Emergency)
            hourly_weights = np.array([
                0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05, 0.07, 0.08, 0.09, 0.09, 0.08,
                0.07, 0.07, 0.06, 0.06, 0.05, 0.05, 0.04, 0.03, 0.02, 0.02, 0.01, 0.01
            ])
            hourly_weights = hourly_weights / hourly_weights.sum()
            hour_counts = np.random.multinomial(expected_patients, hourly_weights)

            occupancy_ratio = min(1.3, expected_patients / max(1, dept["capacity"]))
            base_wait = 15 + max(0, (occupancy_ratio - 0.7)) * 120
            avg_doctors_available = max(1, int(dept["capacity"] / 20 * np.random.uniform(0.7, 1.1)))

            daily_dept_rows.append({
                "date": current_date.date().isoformat(),
                "department": dept["name"],
                "day_of_week": current_date.weekday(),
                "month": current_date.month,
                "expected_patients": expected_patients,
                "capacity": dept["capacity"],
                "occupancy_ratio": round(occupancy_ratio, 3),
                "avg_waiting_time": round(base_wait * np.random.uniform(0.85, 1.15), 1),
                "doctors_available": avg_doctors_available,
                "had_event": 1 if active_event and active_event["department"] == dept["name"] else 0,
                "event_severity": active_event["severity"] if active_event and active_event["department"] == dept["name"] else "none",
            })

            for hour, count in enumerate(hour_counts):
                for _ in range(int(count)):
                    visit_type = "Emergency" if dept["name"] == "Emergency" else random.choices(
                        VISIT_TYPES, weights=[0.4, 0.05, 0.15, 0.3, 0.1]
                    )[0]
                    arrival = current_date.replace(hour=hour, minute=random.randint(0, 59))
                    wait = max(2, np.random.normal(base_wait, base_wait * 0.3))
                    departure = arrival + timedelta(minutes=int(wait) + random.randint(10, 60))
                    visits_rows.append({
                        "patient_age_group": random.choice(AGE_GROUPS),
                        "patient_gender": random.choice(GENDERS),
                        "patient_region": random.choice(REGIONS),
                        "department": dept["name"],
                        "visit_type": visit_type,
                        "arrival_time": arrival.isoformat(),
                        "departure_time": departure.isoformat(),
                        "waiting_time_minutes": round(wait, 1),
                        "visit_status": "completed",
                    })

            # Appointments (subset become no-shows)
            num_appts = int(expected_patients * random.uniform(0.3, 0.5))
            for _ in range(num_appts):
                lead_days = random.randint(0, 21)
                appt_date = current_date + timedelta(days=random.randint(-lead_days, 0))
                no_show_prob = 0.08 + (0.15 if lead_days > 10 else 0) + (0.05 if current_date.weekday() == 0 else 0)
                is_no_show = random.random() < min(0.5, no_show_prob)
                appointments_rows.append({
                    "department": dept["name"],
                    "appointment_date": appt_date.date().isoformat(),
                    "appointment_type": random.choice(["OPD", "Follow-up", "Appointment"]),
                    "lead_time_days": lead_days,
                    "patient_age_group": random.choice(AGE_GROUPS),
                    "day_of_week": appt_date.weekday(),
                    "previous_cancellations": np.random.poisson(0.4),
                    "status": "no_show" if is_no_show else "completed",
                })

    visits_df = pd.DataFrame(visits_rows)
    appts_df = pd.DataFrame(appointments_rows)
    events_df = pd.DataFrame(events_rows)
    daily_df = pd.DataFrame(daily_dept_rows)

    visits_df.to_csv(os.path.join(out_dir, "visits.csv"), index=False)
    appts_df.to_csv(os.path.join(out_dir, "appointments.csv"), index=False)
    events_df.to_csv(os.path.join(out_dir, "hospital_events.csv"), index=False)
    daily_df.to_csv(os.path.join(out_dir, "daily_department_stats.csv"), index=False)

    print("SYNTHETIC / DEMO DATA — not real patient data")
    print(f"visits: {len(visits_df)} rows")
    print(f"appointments: {len(appts_df)} rows")
    print(f"hospital_events: {len(events_df)} rows")
    print(f"daily_department_stats: {len(daily_df)} rows")
    print(f"Saved to: {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=400)
    parser.add_argument("--out", type=str, default="ml/data/raw")
    args = parser.parse_args()
    generate(args.days, args.out)
