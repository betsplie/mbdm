"""
Decisions :     what firms want
Scenarios :     how firms behave
Simulation :    runs the model
"""

import random
from model import Park

def ambition(park, firm):
    """Firm might develop a growth intention. 
    Larger firms have stronger pressure to expand:
    small firm +2%, middle +4%, large +6% for ambition_prob==0.02"""
    probability = (park.cfg.ambition_prob * firm.size)
    firm.growth_intention = (park.rng.random() < probability)
    return firm.growth_intention

def choose_expansion_type(park):
    return (
        "production"                            # choose solar (or battery)
        if park.rng.random() < park.cfg.production_preference
        else "demand"                           # choose electrification (or extra machines)
    )

def expand(park, firm, what):
    """expansion of demand or production"""
    step = park.cfg.expansion_step
    if what == "demand":
        add = firm.demand * step
        if park.headroom() >= add:              # checks if there is still room on the grid
            firm.demand += add                  # assigns growth
            firm.realized_growth += 1
            firm.last_expansion = "demand"
            return True
        firm.unrealized_growth += 1             # no space, then increase unrealized growth
        firm.in_queue = True                    # and put firm in queue
        return False
    # solar expansion
    base = max(firm.production,park.cfg.solar_mean * 0.5)
    firm.production += base * step
    firm.realized_growth += 1
    firm.last_expansion = "production"
    return True


def local_net_load(park, firm):
    """checks sums of demand and production of neighbours (energy hubs)"""
    neigh = park.neighbours(firm)
    return (sum(n.demand for n in neigh) - sum(n.production for n in neigh))


#----------------------
# SCENARIOS
#----------------------

def baseline(park, firm):
    """scenario: self-interest only, no imitation, no coordination"""
    if not ambition(park, firm):
        return
    what = choose_expansion_type(park)
    expand(park, firm, what)

def homophily(park, firm):
    """scenario: competition or intra-branche imitation, firms learn from others in the same branche"""
    if not ambition(park, firm):
        return
    what = choose_expansion_type(park)
    if park.rng.random() < park.cfg.homophily:      # with chance homophily (default==0.5), a firm copies its branche members
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
    if park.rng.random() < park.cfg.coordination:       # with chance coordination, an energy hub is consulted/joined
        firm.cooperation_count += 1                     # firm joined a hub decision
        firm.hub_member = True
        local_net = local_net_load(park,firm,)          # local view of congestion (only neighbours)

        if local_net > 0:                               # demand is larger than production in the neighbourhood (energy is imported)
            if park.rng.random() < park.cfg.coordination_influence:
                what = "production"                     # with chance coordination_influence, firm chooses production
        else:                                           # else: there is more production than demand, so grow
            if park.rng.random() < park.cfg.coordination_influence:
                what = "demand"
    expand(park,firm,what,)


def combined(park, firm):
    """scenario: 1) own preference + 2) homophily + 3) energy hubs"""
    if not ambition(park, firm):
        return

    source = park.rng.choices(
        ["self", "branche", "hub"],
        weights=[
            park.cfg.self_weight,
            park.cfg.branche_weight,
            park.cfg.hub_weight,
        ],
    )[0]

    # own preference
    if source == "self":
        what = choose_expansion_type(park)

    # homophily: what are branch peers doing?
    elif source == "branche":
        what = choose_expansion_type(park)
        peers = [f for f in park.same_branche(firm) if f.last_expansion]
        if peers:
            what = (park.rng.choice(peers).last_expansion)

    # coordination: what does energy hub advice?
    else:
        what = choose_expansion_type(park)
        firm.cooperation_count += 1
        firm.hub_member = True
        local_net = local_net_load(park,firm,)
        if local_net > 0:
            if (park.rng.random() < park.cfg.coordination_influence):
                what = "production"
        else:
            if (park.rng.random() < park.cfg.coordination_influence):
                what = "demand"
    
    expand(park,firm,what,)


RULES = {
    "BASELINE": baseline,
    "HOMOPHILY": homophily,
    "NEIGHBOURS": neighbours,
    "COMBINED": combined,
}

def process_queue(park):
    """queue function: checks if space became available and assigns expansion if so"""
    for firm in park.firms:
        firm.hub_member = False
        if not firm.in_queue:
            continue
        add = (firm.demand * park.cfg.expansion_step)
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