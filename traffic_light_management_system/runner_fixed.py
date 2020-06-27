from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import random
import math
import xml.etree.ElementTree as ET

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa

MAX_STEP = 3600
tree = ET.parse("data/cross2x2.net.xml")
root = tree.getroot()


def generate_routeFile():
    if input("Do you want reproducible tests? (y/n) ") == "y":
        seedValue = int(input("Give a seed number: "))
        random.seed(seedValue)  # make tests reproducible
    # take the row and column numbers to create a matrix representation of the map
    tree = ET.parse("data/cross2x2.net.xml")
    root = tree.getroot()
    maxId = 0
    minTL = math.inf
    for j in root.findall("junction"):
        if j.get("type") != "internal":
            maxId = max(maxId, int(j.get("id")))
        if j.get("type") == "traffic_light":
            minTL = min(minTL, int(j.get("id")))
    cols = int(minTL - 1)
    rows = int((maxId + 5) / (cols + 2) - 2)
    # for maps with different structures
    # rows = int(input("Number of rows: "))
    # cols = int(input("Number of columns: "))
    matrix = []
    for r in range(rows):
        matrix.append([])
        for c in range(cols):
            matrix[r].append(c + r * cols + 1)

    with open("data/cross.rou.xml", "w") as routes:
        print("""<routes>""", file=routes)
        for r in range(1, rows + 1):
            print("""<route id="right{}" edges=" """.format(r), file=routes, end="")
            for c in range(1, cols + 1):
                print("w{}i ".format(matrix[r - 1][c - 1]), file=routes, end="")
            print("""e{}o" />""".format(r * cols), file=routes)

        for r in range(1, rows + 1):
            print("""<route id="left{}" edges=" """.format(r), file=routes, end="")
            for c in range(cols, 0, -1):
                print("e{}i ".format(matrix[r - 1][c - 1]), file=routes, end="")
            print("""w{}o" />""".format(1 + (r - 1) * cols), file=routes)

        for c in range(1, cols + 1):
            print("""<route id="down{}" edges=" """.format(c), file=routes, end="")
            for r in range(1, rows + 1):
                print("n{}i ".format(matrix[r - 1][c - 1]), file=routes, end="")
            print("""s{}o" />""".format(c + (rows - 1) * cols), file=routes)

        for c in range(1, cols + 1):
            print("""<route id="up{}" edges=" """.format(c), file=routes, end="")
            for r in range(rows, 0, -1):
                print("s{}i ".format(matrix[r - 1][c - 1]), file=routes, end="")
            print("""n{}o" />""".format(c), file=routes)

        for r in range(1, rows + 1):
            print(
                """<flow id="WE{}" begin="0" end="{}" number="{}" from="w{}i" to="e{}o" color="{},{},{}" />"""
                    .format(r, MAX_STEP, random.randint(250, 900), 1 + (r - 1) * cols, r * cols,
                            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)
            print(
                """<flow id="EW{}" begin="0" end="{}" number="{}" from="e{}i" to="w{}o" color="{},{},{}" />"""
                    .format(r, MAX_STEP, random.randint(250, 900), r * cols, 1 + (r - 1) * cols,
                            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)
            # print(
            #     """<flow id="WE{}" begin="0" end="{}" probability="{}" from="w{}i" to="e{}o" color="{},{},{}" />"""
            #         .format(r, MAX_STEP, 0.05, 1 + (r - 1) * cols, r * cols,
            #                 random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)
            # print(
            #     """<flow id="EW{}" begin="0" end="{}" probability="{}" from="e{}i" to="w{}o" color="{},{},{}" />"""
            #         .format(r, MAX_STEP, 0.05, r * cols, 1 + (r - 1) * cols,
            #                 random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)

        for c in range(1, cols + 1):
            print(
                """<flow id="NS{}" begin="0" end="{}" number="{}" from="n{}i" to="s{}o" color="{},{},{}" />"""
                    .format(c, MAX_STEP, random.randint(250, 900), c, c + (rows - 1) * cols,
                            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)
            print(
                """<flow id="SN{}" begin="0" end="{}" number="{}" from="s{}i" to="n{}o" color="{},{},{}" />"""
                    .format(c, MAX_STEP, random.randint(250, 900), c + (rows - 1) * cols, c,
                            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)
            # print(
            #     """<flow id="NS{}" begin="0" end="{}" probability="{}" from="n{}i" to="s{}o" color="{},{},{}" />"""
            #         .format(c, MAX_STEP, 1.0, c, c + (rows - 1) * cols,
            #                 random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)
            # print(
            #     """<flow id="SN{}" begin="0" end="{}" probability="{}" from="s{}i" to="n{}o" color="{},{},{}" />"""
            #         .format(c, MAX_STEP, 1.0, c + (rows - 1) * cols, c,
            #                 random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), file=routes)

        print("</routes>", file=routes)


def run():
    edges = set(traci.edge.getIDList())
    tls = traci.trafficlight.getIDList()

    """execute the TraCI control loop"""
    step = 1

    L = 8  # lost time because 2*4
    fixed_flow = 1850

    north_flow = []
    south_flow = []
    east_flow = []
    west_flow = []
    nf_count = []
    sf_count = []
    ef_count = []
    wf_count = []
    for tl in tls:
        north_flow.append(0)
        south_flow.append(0)
        east_flow.append(0)
        west_flow.append(0)
        nf_count.append(set())
        sf_count.append(set())
        ef_count.append(set())
        wf_count.append(set())


    sumWait=0
    total_vehs=0

    totvehswait = 0
    totvehsnumber = 0
    while traci.simulation.getMinExpectedNumber() > 0 and step <= MAX_STEP:
        for e in edges:
            vehsNow = traci.edge.getLastStepVehicleIDs(e)
            for id in vehsNow:
                sumWait += traci.vehicle.getWaitingTime(id)
                total_vehs += 1

        traci.simulationStep()
        step += 1

    print("The total waiting time of vehicles:", sumWait / total_vehs)
    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    optParser.add_option("--waiting-time-memory", default=3600)
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    generate_routeFile()
    # first, generate the route file for this simulation
    # generate_routefile()

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start([sumoBinary, "-c", "data/cross2x2.sumocfg",
                 "--tripinfo-output", "tripinfo.xml"])
    run()
