#%%

import csv
import networkx as nx
import math
import time
from datetime import datetime
from geopy import distance


def distance_sphere(lat1, lng1, lat2, lng2):
    arc = distance.distance((lat1, lng1), (lat2, lng2)).km
    return arc


def dfs_allpaths_iter(G, source, cutoff=None):
    """
    Produce all paths from source in a depth-first-search.

    cutoff = maximum number of nodes in a path.
    """

    if cutoff is None:
        cutoff = 8

    visited = [source]
    stack = [iter(G[source])]

    while stack:
        children = stack[-1]
        child = next(children, None)

        if child is None:
            stack.pop()
            visited.pop()

        elif len(visited) >= cutoff:
            yield list(visited)
            stack.pop()
            visited.pop()

        elif len(visited) < cutoff:
            visited.append(child)
            stack.append(iter(G[child]))

        yield list(visited)


# -----------------------------------------------------------------------------


def construct_GT(n0, G, this_index, this_endtime, cutoff):
    """
    Construct Graph Tree according to start searching node and time.
    """

    global indexx

    if this_index == 0:
        GT.add_node(this_index)
        GT.nodes[this_index]['lat'] = G.nodes[n0]['lat']
        GT.nodes[this_index]['lng'] = G.nodes[n0]['lng']
        GT.nodes[this_index]['color'] = G.nodes[n0]['color']
        GT.nodes[this_index]['endtime'] = this_endtime
        GT.nodes[this_index]['child_list'] = G.neighbors(n0)

    for row in G.neighbors(n0):

        if row != n0:

            indexx += 1

            this_distance = distance_sphere(
                G.nodes[n0]['lat'],
                G.nodes[n0]['lng'],
                G.nodes[row]['lat'],
                G.nodes[row]['lng']
            )

            this_time = this_distance / 3 * 60
            this_endtime1 = this_endtime + this_time

            GT.add_node(indexx)

            GT.nodes[indexx]['lat'] = G.nodes[n0]['lat']
            GT.nodes[indexx]['lng'] = G.nodes[n0]['lng']
            GT.nodes[indexx]['color'] = G.nodes[row]['color']
            GT.nodes[indexx]['endtime'] = this_endtime1
            GT.nodes[indexx]['child_list'] = G.neighbors(row)

            GT.add_edge(this_index, indexx)

            GT[this_index][indexx]['lat1'] = G[n0][row]['lat1']
            GT[this_index][indexx]['lng1'] = G[n0][row]['lng1']
            GT[this_index][indexx]['lat2'] = G[n0][row]['lat2']
            GT[this_index][indexx]['lng2'] = G[n0][row]['lng2']
            GT[this_index][indexx]['pick_p'] = G[n0][row]['pick_p']

            if this_endtime > cutoff:

                GT[this_index][indexx]['seg_g'] = (
                    G[n0][row]['seg_g']
                    * (this_endtime - cutoff)
                    / this_time
                )

            else:

                GT[this_index][indexx]['seg_g'] = G[n0][row]['seg_g']

                construct_GT(
                    row,
                    G,
                    indexx,
                    this_endtime1,
                    cutoff
                )


# -----------------------------------------------------------------------------


def calculat_total_g(G, path):

    total_gg = 0
    pickup_p = 1
    nopick_p = 0

    for n in range(0, len(path) - 1):

        total_gg = total_gg + (
            (
                G[path[n]][path[n + 1]]['seg_g']
                * G[path[n]][path[n + 1]]['pick_p']
            )
            -
            (
                0.18
                * distance_sphere(
                    G.nodes[path[n]]['lat'],
                    G.nodes[path[n]]['lng'],
                    G.nodes[path[n + 1]]['lat'],
                    G.nodes[path[n + 1]]['lng']
                )
                * (1 - G[path[n]][path[n + 1]]['pick_p'])
            )
        ) * pickup_p

        pickup_p = (
            1 - G[path[n]][path[n + 1]]['pick_p']
        ) * pickup_p

    return total_gg


# -----------------------------------------------------------------------------


def dfs_allpaths(G, source, cutoff=None):
    """
    Find the path with the maximum expected earning.

    IMPORTANT:
    max_path stores the exact path found by DFS.
    No zero-padding is used.
    """

    max_fair = 0
    max_path = [source]

    path_iter = dfs_allpaths_iter(G, source, cutoff)

    for path in path_iter:

        status = 1

        # Prevent immediate backtracking:
        # A -> B -> A
        if len(path) > 2:

            for i in range(0, len(path) - 2):

                if path[i] == path[i + 2]:
                    status = 0
                    break

        if status == 1:

            total_g = calculat_total_g(G, path)

            if total_g > max_fair:

                max_fair = total_g

                # IMPORTANT:
                # Store the exact path length.
                # Do NOT use [0] * cutoff.
                max_path = list(path)

    return max_fair, max_path


# -----------------------------------------------------------------------------


def distance1(lat, lng, lat1, lng1, lat2, lng2):

    latt = (float(lat1) + float(lat2)) / 2
    lngg = (float(lng1) + float(lng2)) / 2

    return (
        (float(lat) - latt) ** 2
        +
        (float(lng) - lngg) ** 2
    )


# -----------------------------------------------------------------------------


def start_searching_seg(G, la, ln):

    t = 100000

    t1 = None
    t2 = None

    for n1, n2 in G.edges():

        current_distance = distance1(
            la,
            ln,
            G[n1][n2]['lat1'],
            G[n1][n2]['lng1'],
            G[n1][n2]['lat2'],
            G[n1][n2]['lng2']
        )

        if current_distance < t:

            t = current_distance
            t1 = n1
            t2 = n2

    return t2


# =============================================================================
# LOAD GRAPH
# =============================================================================


G = nx.Graph()

i = 0

with open('../data/refined_vertice.csv', 'r') as f:

    reader = csv.reader(f)

    for row in reader:

        node_id = int(row[0])

        G.add_node(node_id)

        G.nodes[node_id]['lat'] = float(row[1])
        G.nodes[node_id]['lng'] = float(row[2])
        G.nodes[node_id]['color'] = 'white'
        G.nodes[node_id]['total_g'] = 0


j = 0

with open('../data/refined_edges.csv', 'r') as f:

    reader = csv.reader(f)

    for row in reader:

        i = int(row[1])
        j = int(row[2])

        if i < j:

            G.add_edge(
                i,
                j,
                lat1=G.nodes[i]['lat'],
                lng1=G.nodes[i]['lng'],
                lat2=G.nodes[j]['lat'],
                lng2=G.nodes[j]['lng'],
                seg_g=0,
                pick_p=0,
                N_0=0,
                N_1=1,
                fair=0,
                wait_time=[]
            )


with open('../data/network_properties.csv', 'r') as f1:

    reader1 = csv.reader(f1)

    for row in reader1:

        a = int(row[0])
        b = int(row[1])

        G.add_edge(a, b)

        G[a][b]['lat1'] = float(row[2])
        G[a][b]['lng1'] = float(row[3])
        G[a][b]['lat2'] = float(row[4])
        G[a][b]['lng2'] = float(row[5])
        G[a][b]['pick_p'] = float(row[8])
        G[a][b]['seg_g'] = float(row[9])


# =============================================================================
# SEARCHING RANGE
# =============================================================================


min_lat = 39.86
min_lng = 116.31

max_lat = 39.967
max_lng = 116.46

j = 0


# =============================================================================
# QUERY & 50-TAXI SIMULATION
# =============================================================================

query = [
    '20384', '22:57:35', '39.9005705', '116.4966436', '39.9005743', 
    '116.4955831', '39.8984675', '116.484878', '12/1/2013', 
    '22:57:46', '12/1/2013', '22:59:30', '17.7900534\n'
]

start_lat = float(query[2])
start_lng = float(query[3])

# Find starting node
n = start_searching_seg(G, start_lat, start_lng)

# Initialize CSV
writer = csv.writer(open('../results/srrs_50_taxis_response.csv', 'w', newline=''))
writer.writerow(['Taxi_ID', 'Expected_Profit_CNY', 'Suggested_Route'])

print("--- Starting 50-Taxi SRRS Simulation ---")

for taxi in range(1, 51):
    # 1. Find optimal route
    fair, pathss = dfs_allpaths(G, n, 10)
    
    # 2. Extract route safely (handles variable length paths without crashing)
    drive_route = [[G.nodes[node]['lat'], G.nodes[node]['lng']] for node in pathss if node in G]
    
    print(f"Taxi {taxi:02d} | Expected Earning: {fair:.4f} CNY | Route Length: {len(drive_route)} segments")
    writer.writerow([taxi, fair, drive_route])
    
    # 3. Apply SRRS Penalty to the edges to trigger dynamic rerouting
    for k in range(len(pathss) - 1):
        u = pathss[k]
        v = pathss[k+1]
        if 'pick_p' in G[u][v]:
            G[u][v]['pick_p'] *= 0.85