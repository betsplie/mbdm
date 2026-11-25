"""
Decisions :     what firms want
Scenarios :     how firms behave
Simulation :    runs the model
"""

import random
from model import Park

def ambition(park, firm):
    """Firm develops a growth intention. Larger firms have stronger pressure to expand"""
    probability = (park.cfg.ambition_prob * firm.size)
    firm.growth_intention = (park.rng.random() < probability)
    return firm.growth_intention

def choose_expansion_type(park):
    return (
        "production"                            #solar
        if park.rng.random()
           < park.cfg.production_preference
        else "demand"                           #electrification
    )

def expand(park, firm, what):
    step = park.cfg.expansion_step
    if what == "demand":
        add = firm.demand * step
        if park.headroom() >= add:
            firm.demand += add
            firm.realized_growth += 1
            firm.last_expansion = "demand"
            return True
        firm.unrealized_growth += 1
        firm.in_queue = True
        return False
    # solar expansion
    base = max(
        firm.production,
        park.cfg.solar_mean * 0.5
    )
    firm.production += base * step
    firm.realized_growth += 1
    firm.last_expansion = "production"
    return True


def local_net_load(park, firm):
    neigh = park.neighbours(firm)
    return (sum(n.demand for n in neigh) - sum(n.production for n in neigh))


#----------------------
# SCENARIOS
#----------------------

def baseline(park, firm):
    """scenario: self-interest only, no coordination"""
    if not ambition(park, firm):
        return
    what = choose_expansion_type(park)
    expand(park, firm, what)

def homophily(park, firm):
    """scenario: competition or intra-branche imitation, firms learn from others in the same branche"""
    if not ambition(park, firm):
        return
    what = choose_expansion_type(park)

    if park.rng.random() < park.cfg.homophily:
        peers = [
            f for f in park.same_branche(firm)
            if f.last_expansion
        ]
        if peers:
            peer = park.rng.choice(peers)
            what = peer.last_expansion
    expand(park, firm, what)

def neighbours(park, firm):
    """scenario: spatial coordination (energy hubs)"""
    if not ambition(park, firm):
        return
    what = choose_expansion_type(park)
    if park.rng.random() < park.cfg.coordination:
        firm.cooperation_count += 1
        firm.hub_member = True
        local_net = local_net_load(park,firm,)

        # neighbourhood imports lots of power
        # -> stimulate local production
        if local_net > 0:
            if park.rng.random() < park.cfg.coordination_influence:
                what = "production"
        else:
            if park.rng.random() < park.cfg.coordination_influence:
                what = "demand"
    expand(park,firm,what,)


def combined(park, firm):
    """scenario: social learning + spatial coordination"""
    if not ambition(park, firm):
        return
    what = choose_expansion_type(park)

    # Homophily
    if park.rng.random() < park.cfg.homophily:
        peers = [f for f in park.same_branche(firm) if f.last_expansion]
        if peers:
            what = (park.rng.choice(peers).last_expansion)

    # Coordination
    if park.rng.random() < park.cfg.coordination:
        firm.cooperation_count += 1
        firm.hub_member = True
        local_net = local_net_load(park,firm,)
        if local_net > 0:
            if park.rng.random() < park.cfg.coordination_influence:
                what = "production"
        else:
            if park.rng.random() < park.cfg.coordination_influence:
                what = "demand"
    expand(park,firm,what,)


RULES = {
    "BASELINE": baseline,
    "HOMOPHILY": homophily,
    "NEIGHBOURS": neighbours,
    "COMBINED": combined,
}

def process_queue(park):
    for firm in park.firms:
        firm.hub_member = False
        if not firm.in_queue:
            continue
        add = (
            firm.demand
            * park.cfg.expansion_step
        )
        if park.headroom() >= add:
            firm.demand += add
            firm.in_queue = False
            firm.realized_growth += 1

def run_scenario(cfg, seed):
    """runs simulation"""
    rng = random.Random(seed)
    park = Park(cfg, rng)
    rule = RULES[cfg.scenario]
    history = []
    for t in range(cfg.n_ticks):
        process_queue(park)

        deciders = [
            f for f in park.firms
            if rng.random()
            < cfg.decision_share
        ]
        rng.shuffle(deciders)
        for firm in deciders:
            rule(park, firm)
        history.append(
            park.step(t)
        )
    return history, park