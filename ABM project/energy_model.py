"""
Mesa implementation of the Business Park Energy ABM

Social network:
    same branche

Spatial network:
    neighbouring firms

Infrastructure:
    shared grid capacity

Research question:
    how do social learning and neighbour coordination
    affect congestion?
"""

from mesa import Model
from mesa import Agent

from mesa.space import MultiGrid
from mesa.time import RandomActivation

from mesa.datacollection import DataCollector

import random


# ==========================================================
# Firm Agent
# ==========================================================

class FirmAgent(Agent):

    def __init__(
        self,
        unique_id,
        model,
        branche,
        size,
        demand,
        production,
    ):

        super().__init__(unique_id, model)

        self.branche = branche

        self.size = size

        self.demand = demand

        self.production = production

        self.growth_intention = False

        self.last_expansion = None

        self.realized_growth = 0

        self.unrealized_growth = 0

        self.in_queue = False

        self.cooperation_count = 0

        self.hub_member = False


# ==========================================================
# Energy Park Model
# ==========================================================

class EnergyParkModel(Model):

    def __init__(

        self,

        width=12,
        height=12,

        n_branches=4,

        demand_mean=100,

        solar_prob=0.3,
        solar_mean=80,

        grid_capacity=5000,

        ambition_prob=0.02,

        homophily=0.5,

        coordination=0.5,

        decision_share=0.5,

        expansion_step=0.05,

        scenario="COMBINED",

        display_mode="branche",

        seed=None,

    ):

        super().__init__()

        if seed is not None:
            random.seed(seed)

        self.width = width
        self.height = height

        self.grid_capacity = grid_capacity

        self.ambition_prob = ambition_prob

        self.homophily = homophily

        self.coordination = coordination

        self.decision_share = decision_share

        self.expansion_step = expansion_step

        self.scenario = scenario

        self.display_mode = display_mode

        self.grid = MultiGrid(
            width,
            height,
            torus=False,
        )

        self.schedule = RandomActivation(self)

        self.running = True

        # --------------------------------------------------
        # Create firms
        # --------------------------------------------------

        uid = 0

        for x in range(width):
            for y in range(height):

                size = random.randint(1, 3)

                demand = (
                    demand_mean
                    * size
                    * random.uniform(0.5, 1.5)
                )

                production = (
                    solar_mean
                    * random.uniform(0.5, 1.5)
                    if random.random() < solar_prob
                    else 0
                )

                agent = FirmAgent(

                    uid,

                    self,

                    branche=random.randrange(
                        n_branches
                    ),

                    size=size,

                    demand=demand,

                    production=production,

                )

                self.schedule.add(agent)

                self.grid.place_agent(
                    agent,
                    (x, y)
                )

                uid += 1

        # --------------------------------------------------
        # Charts
        # --------------------------------------------------

        self.datacollector = DataCollector(

            model_reporters={

                "Utilization":
                    lambda m:
                    m.utilization(),

                #"Congestion":
                #    lambda m:
                #    m.congestion(),

                 "UnrealizedExpansion":
                    lambda m:
                    sum(
                        a.unrealized_growth
                        for a in m.schedule.agents
                    ),

                "CooperationCount":
                    lambda m:
                    sum(
                        a.cooperation_count
                        for a in m.schedule.agents
                    ),    

                "RealizedGrowth":
                    lambda m:
                    sum(
                        a.realized_growth
                        for a in m.schedule.agents
                    ),

                "QueuedGrowth":
                    lambda m:
                    sum(
                        a.in_queue
                        for a in m.schedule.agents
                    ),

            }

        )

    # ======================================================
    # Metrics
    # ======================================================

    def total_demand(self):

        return sum(
            a.demand
            for a in self.schedule.agents
        )

    def total_production(self):

        return sum(
            a.production
            for a in self.schedule.agents
        )

    def net_load(self):

        return (
            self.total_demand()
            - self.total_production()
        )

    def utilization(self):

        return (
            self.net_load()
            / self.grid_capacity
        )

    def congestion(self):

        return max(
            0,
            self.net_load()
            - self.grid_capacity
        )

    # ======================================================
    # Social network
    # ======================================================

    def same_branche(self, firm):

        return [

            a

            for a in self.schedule.agents

            if (
                a.branche == firm.branche
                and a != firm
            )

        ]

    # ======================================================
    # Model step
    # ======================================================

    def step(self):

        firms = list(
            self.schedule.agents
        )

        random.shuffle(firms)

        for firm in firms:

            if random.random() > self.decision_share:
                continue

            # --------------------------------------
            # growth intention
            # --------------------------------------

            firm.growth_intention = (
                random.random()
                <
                self.ambition_prob
                * firm.size
            )

            if not firm.growth_intention:
                continue

            what = (
                "production"
                if random.random() < 0.4
                else "demand"
            )

            # --------------------------------------
            # homophily
            # --------------------------------------

            if self.scenario in (
                "HOMOPHILY",
                "COMBINED"
            ):

                if (
                    random.random()
                    < self.homophily
                ):

                    peers = [

                        p

                        for p in self.same_branche(
                            firm
                        )

                        if p.last_expansion
                    ]

                    if peers:

                        peer = random.choice(
                            peers
                        )

                        what = (
                            peer.last_expansion
                        )

            # --------------------------------------
            # demand
            # --------------------------------------

            if what == "demand":

                add = (
                    firm.demand
                    * self.expansion_step
                )

                if (
                    self.net_load()
                    + add
                    <= self.grid_capacity
                ):

                    firm.demand += add

                    firm.realized_growth += 1
                    firm.cooperation_count += 1

                    firm.last_expansion = (
                        "demand"
                    )

                else:

                    firm.unrealized_growth += 1

                    firm.in_queue = True

            # --------------------------------------
            # solar
            # --------------------------------------

            else:

                add = max(
                    firm.production,
                    40
                )

                firm.production += (
                    add
                    * self.expansion_step
                )

                firm.realized_growth += 1
                firm.cooperation_count += 1

                firm.last_expansion = (
                    "production"
                )

        self.datacollector.collect(self)