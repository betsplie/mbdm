"""
ABM business park energy
Config :    model parameters
Firm :      agents (businesses)
Park :      environment (the grid of the ABM)
This file only contains model objects.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class Config:

    # environment (grid dimensions)
    width: int = 12
    height: int = 12

    # agents (firms)
    n_branches: int = 4
    demand_mean: float = 100        
    solar_prob: float = 0.3
    solar_mean: float = 80

    # simulations
    n_ticks: int = 200
    n_replications: int = 5
    display_mode: str = "branche"

    # infrastructure
    grid_capacity: float = 30000
    grid_growth: float = 0.0

    # behaviour
    ambition_prob: float = 0.02
    decision_share: float = 0.5
    expansion_step: float = 0.05
    production_preference: float = 0.4
    coordination_influence: float = 0.75

    # scenario's
    homophily: float = 0.5
    coordination: float = 0.5
    scenario: str = "COMBINED"
    radius: int = 1

    seed: Optional[int] = None      #for reproducibility


@dataclass
class Firm:
    id: int
    x: int
    y: int

    branche: int
    size: int

    demand: float
    production: float

    growth_intention: bool = False
    last_expansion: Optional[str] = None
    realized_growth: int = 0
    unrealized_growth: int = 0
    in_queue: bool = False

    # coordination statistics for visualization
    cooperation_count: int = 0
    hub_member: bool = False



class Park:
    def __init__(self, cfg: Config, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.capacity = cfg.grid_capacity
        self.firms: list[Firm] = []
        self.create_firms()

    def create_firms(self):
        idx = 0
        for x in range(self.cfg.width):
            for y in range(self.cfg.height):
                size = self.rng.randint(1, 3)
                
                demand = (
                    self.cfg.demand_mean
                    * size
                    * self.rng.uniform(0.5, 1.5)
                )

                production = (
                    self.cfg.solar_mean
                    * self.rng.uniform(0.5, 1.5)
                    if self.rng.random() < self.cfg.solar_prob
                    else 0
                )

                self.firms.append(
                    Firm(
                        id=idx,
                        x=x,
                        y=y,
                        branche=self.rng.randrange(
                            self.cfg.n_branches
                        ),
                        size=size,
                        demand=demand,
                        production=production,
                    )
                )
                idx += 1

    # helper functions
    def queue_length(self):
        return sum(f.in_queue for f in self.firms)

    def total_demand(self):
        return sum(f.demand for f in self.firms)

    def total_production(self):
        return sum(f.production for f in self.firms)

    def net_load(self):
        return self.total_demand() - self.total_production()

    def headroom(self):
        return self.capacity - self.net_load()

    def overload(self):
        return max(0,self.net_load() - self.capacity)
 
    def same_branche(self, firm):
        """branche network"""
        return [
            f for f in self.firms
            if f.branche == firm.branche
            and f.id != firm.id
        ]

    def neighbours(self, firm):
        """spatial network"""
        r = self.cfg.radius
        return [
            f for f in self.firms
            if (
                f.id != firm.id
                and abs(f.x - firm.x) <= r
                and abs(f.y - firm.y) <= r
            )
        ]

    def step(self, t):
        """update of ABM grid per step"""
        self.capacity *= (1 + self.cfg.grid_growth)
        net = self.net_load()
        overload = self.overload()
        return {
            "t": t,
            "net_load": net,
            "capacity": self.capacity,
            "utilization": net / self.capacity if self.capacity > 0 else 0,
            "overload": overload,
        }

    def load_grid(self):
        grid = np.zeros((self.cfg.width,self.cfg.height))
        for firm in self.firms:
            grid[firm.x,firm.y] = (firm.demand - firm.production)
        return grid