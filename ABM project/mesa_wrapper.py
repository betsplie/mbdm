"""
Mesa wrapper around the core ABM.

The actual model logic lives in:

    model.py
    behaviours.py
    metrics.py

This file only connects that model to Mesa.
"""

import random

from mesa import Model
from mesa.datacollection import DataCollector
from model import Config, Park
from behaviours import (RULES,process_queue,)
from metrics import (branche_segregation,network_alignment,)


class EnergyParkModel(Model):
    def __init__(self, **kwargs):
        super().__init__()

        # ------------------------------------------
        # Create Config from Mesa slider values
        # ------------------------------------------

        self.cfg = Config(**kwargs)
        self.display_mode = self.cfg.display_mode
        self.rng = random.Random(self.cfg.seed)
        self.park = Park(self.cfg,self.rng,)
        self.running = True

        # ------------------------------------------
        # Mesa charts
        # ------------------------------------------

        self.datacollector = DataCollector(
            model_reporters={
                "Utilization":

                    lambda m:
                    m.park.net_load()
                    / m.park.capacity

                    if m.park.capacity > 0
                    else 0,

                "Congestion":

                    lambda m:
                    m.park.overload(),

                "RealizedGrowth":

                    lambda m:
                    sum(
                        f.realized_growth
                        for f in m.park.firms
                    ),

                "QueuedGrowth":

                    lambda m:
                    m.park.queue_length(),

                "Segregation":

                    lambda m:
                    branche_segregation(
                        m.park
                    ),

                "Alignment":

                    lambda m:
                    network_alignment(
                        m.park
                    ),

            }
        )

    def step(self):
        process_queue(self.park)
        rule = RULES[self.cfg.scenario]
        deciders = [f for f in self.park.firms if self.rng.random() < self.cfg.decision_share]

        self.rng.shuffle(deciders)

        for firm in deciders:
            rule(self.park,firm,)
        self.park.step(self.steps)
        self.datacollector.collect(self)