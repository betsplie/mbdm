"""
ABM business park energy
Config :    model parameters: what does the business park we're modeling look like
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
    # environment (grid dimensions = no of firms)
    width: int = 12
    height: int = 12

    # agents (firms)
    n_branches: int = 4                     # no of sectors we distinguish (eg logistics, production, food, technology)
    demand_mean: float = 100                # avg electricity use of 1 firm: if it's higher there is more pressure on the grid   
    solar_prob: float = 0.3                 # % chance that a company already has PV
    solar_mean: float = 80                  # avg production of PV

    # simulations
    n_ticks: int = 200                      # timesteps in simulation (could be days, months, years)
    n_replications: int = 5     
    display_mode: str = "branche"

    # infrastructure
    grid_capacity: float = 30000            # max capacity of our virtual grid
    grid_growth: float = 0.0                # grid expansion, is not modeled now

    # behaviour
    ambition_prob: float = 0.02             # proxy for innovation: chance that firm wants to expand
    decision_share: float = 0.5             # % of firms that make a decision per timestep
    expansion_step: float = 0.05            # % of increase in production or demand per expansion
    production_preference: float = 0.4      # % chance company wants to expand production (instead of demand)
    coordination_influence: float = 0.75    # % of times coordination is successful (eg following advice of energy hub)

    # scenario's
    homophily: float = 0.5                  # chance that a firm goes for competition (imitating firms in same branche)
    coordination: float = 0.5               # chance that firm chooses local cooperation (joins energy hub)
    scenario: str = "COMBINED"
    radius: int = 1                         # defines who neighbours are (=Moore8) 
    self_weight: float = 0.4                       # chance that self-interest is pursued (in combined scenario)
    branche_weight: float = 0.3                    # chance that branche competition is chosen (in combined scenario)
    hub_weight: float = 0.3                        # chance that firm coordinates with energy hub (in combined scenario)

    seed: Optional[int] = None              # for reproducibility


@dataclass
class Firm:                                 # these are our agents (firms)
    id: int
    x: int                                  # coordinates
    y: int

    branche: int
    size: int                               # (1,2,3) = small, mkb, large firm

    demand: float
    production: float
    # currently implemented: demand - production = grid pressure

    growth_intention: bool = False
    last_expansion: Optional[str] = None    # last time did it increase demand or production (used for homophily)
    realized_growth: int = 0                # growth that happened (cumulative)
    unrealized_growth: int = 0              # growth that could not happen due to congestion
    in_queue: bool = False                  # is firm in queue for expansion?

    # coordination statistics for visualization
    cooperation_count: int = 0              # no of times firm participated in energy hub coordination
    hub_member: bool = False


class Park:                                 # this is the environment (virtual business park)
    def __init__(self, cfg: Config, rng: random.Random):
        self.cfg = cfg
        self.rng = rng
        self.capacity = cfg.grid_capacity   # baseline grid capacity of the park
        self.firms: list[Firm] = []         # list with all firms on business park
        self.create_firms()
        self.initial_load = self.net_load()
        self.initial_utilization = (self.initial_load / self.capacity)


    def create_firms(self):
        """creates the business park and fills it with different firms"""
        idx = 0
        for x in range(self.cfg.width):
            for y in range(self.cfg.height):
                size = self.rng.randint(1, 3)
                demand = (                  # large firm has higher demand, but with some variation
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
                        branche=self.rng.randrange(self.cfg.n_branches),    # branches are randomly assigned
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
        """demand - production = how much energy comes from grid"""
        return self.total_demand() - self.total_production()

    def headroom(self):     # space available on the grid
        return self.capacity - self.net_load()

    def overload(self):     # grid congestion
        return max(0,self.net_load() - self.capacity)
 
    def same_branche(self, firm):
        """branche network: firms imitate each other within branches"""
        return [
            f for f in self.firms
            if f.branche == firm.branche
            and f.id != firm.id
        ]

    def neighbours(self, firm):
        """spatial network: firms on adjacent lots"""
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
        """update of ABM grid per step and save metrics for plots"""
        self.capacity *= (1 + self.cfg.grid_growth)     # does not do anything is growth == 0
        net = self.net_load()                           # current load of grid
        overload = self.overload()                      # current congestion
        return {
            "t": t,
            "net_load": net,
            "capacity": self.capacity,
            "utilization": net / self.capacity if self.capacity > 0 else 0,
            "overload": overload,
        }

    def load_grid(self):
        """saves metrics for heat map"""
        grid = np.zeros((self.cfg.width,self.cfg.height))
        for firm in self.firms:
            grid[firm.x,firm.y] = (firm.demand - firm.production)
        return grid