from typing import Dict, Type
from app.engines.energy.provider import EnergyMeasurementProvider, MeasurementMode
from app.engines.energy.estimated_provider import EstimatedEnergyProvider, EstimationCoefficients
from app.engines.energy.hardware_providers import (
    RaplEnergyProvider,
    KeplerEnergyProvider,
    ExternalMeterProvider,
)


_PROVIDER_REGISTRY: Dict[str, Type[EnergyMeasurementProvider]] = {
    "estimated": EstimatedEnergyProvider,
    "rapl": RaplEnergyProvider,
    "kepler": KeplerEnergyProvider,
    "external": ExternalMeterProvider,
}

_default_provider: EnergyMeasurementProvider | None = None


def get_provider(name: str = "estimated", coefficients: EstimationCoefficients | None = None) -> EnergyMeasurementProvider:
    name = name.lower()
    if name not in _PROVIDER_REGISTRY:
        available = ", ".join(sorted(_PROVIDER_REGISTRY.keys()))
        raise ValueError(f"Unknown energy provider '{name}'. Available: {available}")

    cls = _PROVIDER_REGISTRY[name]

    if name == "estimated":
        return cls(coefficients=coefficients)
    return cls()


def get_default_provider() -> EnergyMeasurementProvider:
    global _default_provider
    if _default_provider is None:
        from app.config import settings
        coefficients = settings.get_estimation_coefficients()
        _default_provider = get_provider(settings.ENERGY_PROVIDER, coefficients=coefficients)
    return _default_provider


def reset_default_provider() -> None:
    global _default_provider
    _default_provider = None


def list_providers() -> dict:
    return {
        name: {
            "class": cls.__name__,
            "available": cls().is_available(),
            "mode": cls().get_mode().value,
        }
        for name, cls in _PROVIDER_REGISTRY.items()
    }
