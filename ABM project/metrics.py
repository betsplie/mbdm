"""
Metrics : measures output
Social network: branche (competition)
Spatial network: neighbours (energy hubs)
"""

import numpy as np

def branche_segregation(park):
    """Schelling-style segregation: measures how often firms are surrounded by same-branche firms"""
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


def summarize(history, park):
    util = [h["utilization"] for h in history]
    return {
        "mean_utilization": np.mean(util),      # how heavily is the grid used
        "max_utilization": np.max(util),        # how close are we to congestion
        "congestion_share": np.mean([h["overload"] > 0 for h in history]),
        "realized_expansion": sum(f.realized_growth for f in park.firms),     # actual growth achieved
        "unrealized_expansion": sum(f.unrealized_growth for f in park.firms),   # lost opportunities to grow
        "queue_length": park.queue_length(),
        "cooperation_count": sum(f.cooperation_count for f in park.firms),      # amount of local coordination
        #"branche_segregation": branche_segregation(park),
        #"network_alignment": network_alignment(park),
        "demand_expansions": sum(1 for f in park.firms if f.last_expansion == "demand"),
        "solar_expansions":sum(1 for f in park.firms if f.last_expansion == "production"),
        "cooperation_count": sum(f.cooperation_count for f in park.firms)
    }