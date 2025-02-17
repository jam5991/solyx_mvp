from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import aiohttp
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class EnergyTracker:
    """Tracks energy prices and optimal execution windows"""
    
    def __init__(self):
        self.price_cache: Dict[str, Tuple[datetime, float]] = {}
        self.cache_duration = timedelta(minutes=15)
        
    async def get_current_cost(self, region: str) -> float:
        """Get the current energy cost for a region (USD/kWh)"""
        # Check cache first
        if region in self.price_cache:
            timestamp, price = self.price_cache[region]
            if datetime.now() - timestamp < self.cache_duration:
                return price

        try:
            price = await self._fetch_energy_price(region)
            self.price_cache[region] = (datetime.now(), price)
            return price
        except Exception as e:
            logger.error(f"Error fetching energy price for {region}: {e}")
            # Return last known price or default
            return self.price_cache.get(region, (None, 0.12))[1]

    async def _fetch_energy_price(self, region: str) -> float:
        """Fetch real-time energy prices from grid APIs"""
        if region.startswith("caiso"):
            return await self._fetch_caiso_price()
        elif region.startswith("ercot"):
            return await self._fetch_ercot_price()
        else:
            return 0.12  # Default price if region unknown

    async def _fetch_caiso_price(self) -> float:
        """Fetch CAISO energy prices"""
        # Simplified for example - would need real API integration
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.caiso.com/prices") as resp:
                    data = await resp.json()
                    return float(data["current_price"])
        except Exception as e:
            logger.error(f"CAISO API error: {e}")
            return 0.12

    async def _fetch_ercot_price(self) -> float:
        """Fetch ERCOT energy prices"""
        # Similar implementation for ERCOT
        return 0.10

    async def find_optimal_execution_window(
        self, 
        region: str, 
        duration_hours: int,
        max_delay_hours: int = 24
    ) -> Optional[datetime]:
        """Find the optimal time window to execute a job based on energy prices"""
        try:
            # Fetch price forecasts for the next max_delay_hours
            forecasts = await self._get_price_forecasts(region, max_delay_hours)
            
            if not forecasts:
                return datetime.now()  # If no forecast, start immediately

            # Find window with lowest average price
            window_prices = []
            for i in range(len(forecasts) - duration_hours + 1):
                window = forecasts[i:i + duration_hours]
                avg_price = sum(window) / len(window)
                window_prices.append((avg_price, i))

            best_price, best_start = min(window_prices, key=lambda x: x[0])
            start_time = datetime.now() + timedelta(hours=best_start)
            
            logger.info(f"Found optimal window starting at {start_time} "
                       f"with average price ${best_price:.3f}/kWh")
            return start_time

        except Exception as e:
            logger.error(f"Error finding optimal window: {e}")
            return datetime.now()

    async def _get_price_forecasts(self, region: str, hours: int) -> list[float]:
        """Get energy price forecasts for the specified hours"""
        # This would integrate with actual grid APIs
        # Returning mock data for now
        import random
        return [0.10 + random.random() * 0.05 for _ in range(hours)]
