"""
Metrics : measures output of behaviour
Social network: branche (competition)
Spatial network: neighbours (energy hubs)
"""

import numpy as np

def branche_segregation(park):
    """Schelling-style segregation: measures how often firms are surrounded by same-branche firms (clustering)"""
    scores = []
    for firm in park.firms:
        neigh = park.neighbours(firm)
        if not neigh:
            continue
        same = sum(1 for n in neigh if n.branche == firm.branche)
        scores.append(same / len(neigh))
    return np.mean(scores) if scores else 0


def network_alignment(park):
    """Overlap between social network (same branche) and spatial network (neighbours)"""
    scores = []
    for firm in park.firms:
        spatial = {n.id for n in park.neighbours(firm)}
        social = {n.id for n in park.same_branche(firm)}
        union = spatial | social
        if not union:
            continue
        scores.append(len(spatial & social) / len(union))
    return np.mean(scores) if scores else 0


def summarize(history, park):                                                       # history = what happened during simulation, park = final state
    util = [h["utilization"] for h in history]
    return {
        "mean_utilization": np.mean(util),                                          # how heavily is the grid used on average (in %)
        "max_utilization": np.max(util),                                            # peak use: how close are we to congestion
        "realized_expansion": sum(f.realized_growth for f in park.firms),           # actual growth achieved
        "unrealized_expansion": sum(f.unrealized_growth for f in park.firms),       # cumulative count of blocked expansion attempts due to grid congestion
        "queue_length": park.queue_length(),                                        # no of firms currently waiting for grid capacity
        "cooperation_count": sum(f.cooperation_count for f in park.firms),          # amount of local coordination, no of times hub is joined (or consulted)
        "final_demand": park.total_demand(),                                        # total electricity demand at end of simulation (how much elektrification happened)
        "final_production": park.total_production(),                                # total local production at end of simulation (how much local production is stimulated)
        "initial_load": park.initial_load,                                          # energy demand of park at t==0
        "initial_utilization": park.initial_utilization,                            # % of grid capacity used at t==0
        #"congestion_share": np.mean([h["overload"] > 0 for h in history]),         # % time steps with overload (congestion)
        #"branche_segregation": branche_segregation(park),
        #"network_alignment": network_alignment(park),
        #"demand_expansions": sum(1 for f in park.firms if f.last_expansion == "demand"),
        #"solar_expansions":sum(1 for f in park.firms if f.last_expansion == "production")
    }