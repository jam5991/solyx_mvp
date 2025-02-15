from datetime import datetime
from typing import Dict, Optional
from ..database.models import GPUInstance


class EnergyTracker:
    # Approximate TDP (Thermal Design Power) for different GPU types in watts
    GPU_POWER_CONSUMPTION = {
        "A100": 400,
        "V100": 300,
        "A6000": 300,
        "A5000": 230,
        "A4000": 140,
        "RTX_4090": 450,
        "RTX_3090": 350,
    }

    # Default power consumption if GPU type is unknown
    DEFAULT_POWER_CONSUMPTION = 300  # watts

    def __init__(self):
        # Cache for regional energy costs (USD per kWh)
        self.regional_energy_costs = {
            "us-east": 0.12,
            "us-west": 0.14,
            "eu-west": 0.20,
            "ap-east": 0.18,
            # Add more regions as needed
        }

    def get_gpu_power_consumption(self, gpu_type: str) -> float:
        """Get the power consumption in watts for a given GPU type"""
        # Normalize GPU type string
        normalized_type = gpu_type.upper().replace("-", "_")
        return self.GPU_POWER_CONSUMPTION.get(
            normalized_type, self.DEFAULT_POWER_CONSUMPTION
        )

    def get_energy_cost(self, region: str) -> float:
        """Get the energy cost per kWh for a given region"""
        return self.regional_energy_costs.get(region, 0.15)  # Default to 0.15 USD/kWh

    def calculate_energy_cost(
        self, gpu_instance: GPUInstance, duration_hours: float
    ) -> Dict[str, float]:
        """Calculate energy cost and consumption for a GPU instance"""
        power_consumption = self.get_gpu_power_consumption(gpu_instance.gpu_type)
        energy_rate = self.get_energy_cost(gpu_instance.region)

        # Calculate energy consumption in kWh
        energy_consumed = (power_consumption * duration_hours) / 1000

        # Calculate cost
        energy_cost = energy_consumed * energy_rate

        return {
            "energy_consumed_kwh": energy_consumed,
            "energy_cost_usd": energy_cost,
            "power_consumption_watts": power_consumption,
            "energy_rate_kwh": energy_rate,
        }
