from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import json


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "Carbon Guard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./carbon_guard.db"

    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'

    DEFAULT_CARBON_INTENSITY: float = 475.0
    DEFAULT_RENEWABLE_PERCENTAGE: float = 25.0
    DEFAULT_ENERGY_CONSUMPTION_KWH: float = 0.5

    MINIMUM_SAVINGS_THRESHOLD: float = 0.01
    MAX_DELAY_HOURS: int = 4

    ENERGY_PROVIDER: str = "estimated"
    ENERGY_BASE_POWER_WATTS: float = 100.0
    ENERGY_CPU_COEFFICIENT: float = 3.0
    ENERGY_MEMORY_COEFFICIENT: float = 0.5
    ENERGY_NETWORK_COEFFICIENT: float = 0.1
    ENERGY_WORKLOAD_COUNT_COEFFICIENT: float = 5.0
    ENERGY_CONTROL_BASE_OVERHEAD_WATTS: float = 2.0
    ENERGY_CONTROL_INTENSITY_MULTIPLIER: float = 1.5

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    def get_estimation_coefficients(self):
        from app.engines.energy.estimated_provider import EstimationCoefficients
        return EstimationCoefficients(
            base_power_watts=self.ENERGY_BASE_POWER_WATTS,
            cpu_coefficient=self.ENERGY_CPU_COEFFICIENT,
            memory_coefficient=self.ENERGY_MEMORY_COEFFICIENT,
            network_coefficient=self.ENERGY_NETWORK_COEFFICIENT,
            workload_count_coefficient=self.ENERGY_WORKLOAD_COUNT_COEFFICIENT,
            control_base_overhead_watts=self.ENERGY_CONTROL_BASE_OVERHEAD_WATTS,
            control_intensity_multiplier=self.ENERGY_CONTROL_INTENSITY_MULTIPLIER,
        )


settings = Settings()
