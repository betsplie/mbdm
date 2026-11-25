"""
Browser visualization for the Business Park Energy ABM

Interactive Mesa dashboard.

All default parameter values come from Config in model.py.
"""

import colorsys
from mesa.visualization.modules import (CanvasGrid,ChartModule,)
from mesa.visualization.ModularVisualization import (ModularServer,)
try:
    from mesa.visualization.UserParam import (Slider,Choice,)
except Exception:
    from mesa.visualization.UserParam import (UserSettableParameter as Slider)

from model import Config
#from mesa_wrapper import (EnergyParkModel,)
from energy_model import (
    EnergyParkModel,
    FirmAgent,
)
CFG = Config()

# ==========================================================
# Colours
# ==========================================================

def branche_colour(branche):
    """
    Give each branche a stable colour. Makes it easy to see whether segregation emerges spatially.
    """

    hue = branche / max(CFG.n_branches * 2, 8)
    r, g, b = colorsys.hsv_to_rgb(hue,0.85,0.95,)
    return (
        f"#{int(r*255):02x}"
        f"{int(g*255):02x}"
        f"{int(b*255):02x}"
    )


# ==========================================================
# Agent visualization
# ==========================================================

def agent_portrayal(agent):
    if agent is None:
        return None
    mode = agent.model.display_mode

    if mode == "branche":
        colour = branche_colour(agent.branche)

    elif mode == "expansion":
        if agent.last_expansion == "demand":
            colour = "#d62728"
        elif agent.last_expansion == "production":
            colour = "#2ca02c"
        else:
            colour = "#cccccc"

    elif mode == "net_load":
        net = (agent.demand - agent.production)
        if net <= 0:
            colour = "#2166ac"
        elif net < 100:
            colour = "#67a9cf"
        elif net < 200:
            colour = "#fddbc7"
        else:
            colour = "#b2182b"

    elif mode == "energy_hubs":
        coop = agent.cooperation_count
        if coop == 0:
            colour = "#f0f0f0"
        elif coop < 3:
            colour = "#c7e9c0"
        elif coop < 6:
            colour = "#74c476"
        else:
            colour = "#006d2c"
    elif mode == "growth":
        if agent.unrealized_growth == 0:
            colour = "#e5f5e0"
        elif agent.unrealized_growth < 3:
            colour = "#a1d99b"
        elif agent.unrealized_growth < 6:
            colour = "#31a354"
        else:
            colour = "#006d2c"

    else:
        colour = "#cccccc"

    return {
        "Shape": "rect",
        "Filled": "true",
        "Layer": 0,
        "w": 1,
        "h": 1,
        "Color": colour,
        "text": "",
        "text_color": "black",
    }

# ==========================================================
# Grid visualization
# ==========================================================

grid = CanvasGrid(
    agent_portrayal,
    CFG.width,
    CFG.height,
    600,    # pixels
    600,
)

# ==========================================================
# Charts
# ==========================================================

capacity_chart = ChartModule(
    [
        {
            "Label": "Utilization",
            "Color": "Blue",
        },

        #{
        #    "Label": "UnrealizedExpansion",
        #    "Color": "Red",
        #},

    ],

    data_collector_name="datacollector",
)


growth_chart = ChartModule(
    [
        {
            "Label": "RealizedGrowth",
            "Color": "Green",
        },
        {
            "Label": "QueuedGrowth",
            "Color": "Orange",
        },
        {    
            "Label": "UnrealizedExpansion",
            "Color": "Red",
        },
    ],
    data_collector_name="datacollector",
)

cooperation_chart = ChartModule(

    [

        {
            "Label": "CooperationCount",
            "Color": "Purple",
        },

    ],

    data_collector_name="datacollector",
)

network_chart = ChartModule(
    [
        {
            "Label": "Segregation",
            "Color": "Purple",
        },
        {
            "Label": "Alignment",
            "Color": "Black",
        },
    ],
    data_collector_name="datacollector",
)

# ==========================================================
# model parameters
# ==========================================================

model_params = {

    "display_mode":
    Choice(
        "Display Mode",
        value=CFG.display_mode,
        choices=[
            "branche",
            "expansion",
            "net_load",
            "energy_hubs",
            "growth",
        ],
    ),

    "width":Slider("Grid width",CFG.width,5,30,1,),
    "height":Slider("Grid height",CFG.height,5,30,1,),

    "n_branches":
        Slider("Number of branches",CFG.n_branches,2,10,1,),


    "grid_capacity":
        Slider("Grid capacity",CFG.grid_capacity,1000,50000,500,),


    "ambition_prob":
        Slider(
            "Growth pressure",
            CFG.ambition_prob,
            0.00,
            0.20,
            0.01,
        ),

    # ----------------------------------------------
    # Homophily
    # ----------------------------------------------

    "homophily":

        Slider(
            "Homophily (h)",
            CFG.homophily,
            0.00,
            1.00,
            0.05,
        ),

    # ----------------------------------------------
    # Coordination
    # ----------------------------------------------

    "coordination":
        Slider(
            "Coordination (c)",
            CFG.coordination,
            0.00,
            1.00,
            0.05,
        ),

    # ----------------------------------------------
    # Expansion size
    # ----------------------------------------------

    "expansion_step":
        Slider(
            "Expansion step",
            CFG.expansion_step,
            0.01,
            0.20,
            0.01,
        ),

    # ----------------------------------------------
    # Scenario choice
    # ----------------------------------------------

    "scenario":
        Choice(
            "Scenario",
            value=CFG.scenario,
            choices=[
                "Baseline",
                "Branche competition",
                "Local cooperation",
                "Combined",
            ],
        ),
}


# ==========================================================
# Server
# ==========================================================

def make_server():
    server = ModularServer(
        EnergyParkModel,
        [
            grid,
            capacity_chart,
            growth_chart,
            cooperation_chart,

        ],

        "Business Park Energy ABM",
        model_params,
    )

    server.port = 8521
    return server


# ==========================================================
# Launch
# ==========================================================

if __name__ == "__main__":

    make_server().launch()