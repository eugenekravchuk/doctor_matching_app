from collections import defaultdict
import networkx as nx
import random
EPSILON = 1e-5
PENALTY_MULTIPLIER = 1.5

def bellman_ford(G, residual, costs, doctor_penalty, cabinet_penalty, source, sink):
    dist = {node: float('inf') for node in residual}
    dist[source] = 0
    parent = {node: None for node in residual}

    for _ in range(len(residual) - 1):
        for u in residual:
            for v in residual[u]:
                if not residual[u][v]:
                    continue 

                doctor, loc, cab, cost = None, None, None, 0

                if G.nodes[u].get('type') == 'doctor_shift' and G.nodes[v].get('type') == 'loc_cab_shift':
                    doctor = u[0]
                    loc = v[0]
                    cab = v[1]

                    cost = costs[doctor][loc]
                    costs[loc][doctor] = cost
                    cost += (doctor_penalty[doctor] + cabinet_penalty.get((loc, cab), 0)) * PENALTY_MULTIPLIER

                elif G.nodes[u].get('type') == 'loc_cab_shift' and G.nodes[v].get('type') == 'doctor_shift':
                    doctor = v[0]
                    loc = u[0]
                    
                    cost = -costs[loc][doctor]

                
                cost += random.uniform(0, EPSILON)

                if dist[u] + cost < dist[v]:
                    dist[v] = dist[u] + cost
                    parent[v] = u

    if dist[sink] == float('inf'):
        return None, None

    path = []
    current_node = sink
    while current_node is not None:
        path.append(current_node)
        current_node = parent[current_node]

    path.reverse()
    return dist[sink], path


def min_cost_max_flow(G: nx.DiGraph, costs, doctor_penalty, cabinet_penalty, necessary_shifts, schedule, source: str, sink: str):
    residual = defaultdict(lambda: defaultdict(int))

    

    for u, v, data in G.edges(data=True):
        residual[u][v] = data.get('capacity', 1)
        residual[v][u] = 0

    max_flow = 0
    min_cost = 0

    for doctor in necessary_shifts:
        for location, cab, shift in necessary_shifts[doctor]:
            residual[source][doctor] -= 1
            residual[doctor][(doctor, shift)] -= 1
            residual[(doctor, shift)][(location, cab, shift)] -= 1
            residual[(location, cab, shift)][sink] -= 1

            cabinet_penalty[(location, cab)] += 1

            schedule[location][cab][shift] = doctor

        doctor_penalty[doctor] += len(necessary_shifts[doctor])
        max_flow += len(necessary_shifts[doctor])

    while True:
        _, path = bellman_ford(G, residual, costs, doctor_penalty, cabinet_penalty, source, sink)

        if path is None:
            break

        path_flow = float('inf')
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            path_flow = min(path_flow, residual[u][v])
    

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            residual[u][v] -= path_flow
            residual[v][u] += path_flow

            doctor, loc, cab, shift, cost = None, None, None, None, 0
            reversed = False
    
            if G.nodes[u].get('type') == 'doctor_shift' and G.nodes[v].get('type') == 'loc_cab_shift':
                doctor = u[0]
                loc, cab, shift = v

            elif G.nodes[u].get('type') == 'loc_cab_shift' and G.nodes[v].get('type') == 'doctor_shift':
                doctor = v[0]
                loc, cab, shift = u
                reversed = True

            if doctor is not None and loc is not None:
                # print(f"Processing doctor: {doctor}, loc: {loc}, cab: {cab}, shift: {shift}, reversed: {reversed}")
                # print(costs[loc])
                # print(costs[doctor][loc], costs[loc][doctor], doctor_penalty[doctor], cabinet_penalty.get((loc, cab), 0))

                if not reversed:
                    cost = costs[doctor][loc]
                    cost += (doctor_penalty[doctor] + cabinet_penalty.get((loc, cab), 0)) * PENALTY_MULTIPLIER

                    schedule[loc][cab][shift] = doctor
                
                else:
                    cost = -costs[loc][doctor]

                    schedule[loc][cab][shift] = None

                doctor_penalty[doctor] += 1 if not reversed else -1
                cabinet_penalty[(loc, cab)] += 1 if not reversed else -1


            min_cost += cost * path_flow

        max_flow += path_flow


    return max_flow, min_cost, schedule


    

