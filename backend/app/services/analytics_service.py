import random
from datetime import datetime, timedelta, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AnalyticsService:
    def get_security_analytics(self, period: str = "7d") -> dict:
        return {
            "attacks_over_time": self._generate_time_series(period),
            "categories": [
                {"type": "DDoS", "count": random.randint(5, 15)},
                {"type": "Brute Force", "count": random.randint(3, 10)},
                {"type": "Port Scan", "count": random.randint(8, 20)},
                {"type": "SQL Injection", "count": random.randint(2, 8)},
                {"type": "Malware", "count": random.randint(1, 5)},
                {"type": "Suspicious Login", "count": random.randint(4, 12)},
            ],
            "severity_dist": [
                {"level": "CRITICAL", "count": random.randint(1, 5)},
                {"level": "HIGH", "count": random.randint(3, 10)},
                {"level": "MEDIUM", "count": random.randint(5, 15)},
                {"level": "LOW", "count": random.randint(8, 20)},
            ],
            "top_sources": [
                {"ip": "192.168.1.100", "count": random.randint(5, 20)},
                {"ip": "10.0.0.50", "count": random.randint(3, 15)},
                {"ip": "172.16.0.25", "count": random.randint(2, 10)},
            ],
        }

    def get_carbon_analytics(self, period: str = "7d") -> dict:
        return {
            "emissions_over_time": self._generate_carbon_series(period),
            "savings_over_time": self._generate_savings_series(period),
            "efficiency_trend": self._generate_efficiency_series(period),
        }

    def get_energy_analytics(self, period: str = "7d") -> dict:
        return {
            "usage_over_time": self._generate_energy_series(period),
            "by_type": [
                {"type": "Security Operations", "energy_kwh": round(random.uniform(0.5, 2.0), 2)},
                {"type": "Monitoring", "energy_kwh": round(random.uniform(0.3, 1.5), 2)},
                {"type": "Analysis", "energy_kwh": round(random.uniform(0.2, 1.0), 2)},
                {"type": "Other", "energy_kwh": round(random.uniform(0.1, 0.5), 2)},
            ],
            "peak_hours": [
                {"hour": h, "energy_kwh": round(random.uniform(0.1, 0.5), 2)}
                for h in range(24)
            ],
        }

    def get_optimization_analytics(self) -> dict:
        return {
            "runs": random.randint(5, 20),
            "avg_reduction": round(random.uniform(15, 35), 1),
            "total_saved_kg": round(random.uniform(5, 25), 2),
            "best_reduction": round(random.uniform(30, 50), 1),
        }

    def _generate_time_series(self, period: str) -> list:
        days = {"24h": 1, "7d": 7, "30d": 30}.get(period, 7)
        now = _utcnow()
        return [
            {"date": (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
             "count": random.randint(2, 15)}
            for i in range(days)
        ]

    def _generate_carbon_series(self, period: str) -> list:
        days = {"24h": 1, "7d": 7, "30d": 30}.get(period, 7)
        now = _utcnow()
        return [
            {"date": (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
             "co2_kg": round(random.uniform(0.5, 3.0), 2)}
            for i in range(days)
        ]

    def _generate_savings_series(self, period: str) -> list:
        days = {"24h": 1, "7d": 7, "30d": 30}.get(period, 7)
        now = _utcnow()
        cumulative = 0
        result = []
        for i in range(days):
            saved = round(random.uniform(0.1, 1.5), 2)
            cumulative += saved
            result.append({
                "date": (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
                "saved_kg": saved,
                "cumulative_kg": round(cumulative, 2),
            })
        return result

    def _generate_efficiency_series(self, period: str) -> list:
        days = {"24h": 1, "7d": 7, "30d": 30}.get(period, 7)
        now = _utcnow()
        return [
            {"date": (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
             "efficiency": round(random.uniform(55, 90), 1)}
            for i in range(days)
        ]

    def _generate_energy_series(self, period: str) -> list:
        days = {"24h": 1, "7d": 7, "30d": 30}.get(period, 7)
        now = _utcnow()
        return [
            {"date": (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"),
             "energy_kwh": round(random.uniform(1.0, 5.0), 2)}
            for i in range(days)
        ]
