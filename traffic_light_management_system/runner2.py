#!/usr/bin/env python
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2009-2020 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    runner.py
# @author  Lena Kalleske
# @author  Daniel Krajzewicz
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @date    2009-03-26

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import random

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa

MAX_STEP = 3600


def generate_routefile():
    # random.seed(42)  # make tests reproducible
    # demand per second from different directions

    # maxrand = 8
    with open("data/cross.rou.xml", "w") as routes:
        print("""<routes>

        <route id="right" edges="w1i w2i e2o" />
        <route id="left" edges="e2i e1i w1o" />
        <route id="down" edges="n1i n3i s3o" />
        <route id="up" edges="s3i s1i n1o" />
        
        <route id="right2" edges="w3i w4i e4o" />
        <route id="left2" edges="e4i e3i w3o" />
        <route id="down2" edges="n2i n4i s4o" />
        <route id="up2" edges="s4i s2i n2o" />
        
        <flow id="WE" begin="0" end="3600"  number="404" from="w1i" to="e2o" color="1,0,0"/>
        <flow id="EW" begin="0" end="3600"  number="836" from="e2i" to="w1o" color="1,0,0"/>
        <flow id="WE2" begin="0" end="3600" number="666" from="w3i" to="e4o" color="1,0,0"/>
        <flow id="EW2" begin="0" end="3600" number="576" from="e4i" to="w3o" color="1,0,0"/>
        
        <flow id="NS" begin="0" end="3600"  number="463" from="n1i" to="s3o"/>
        <flow id="SN" begin="0" end="3600"  number="586" from="s3i" to="n1o"/>
        <flow id="NS2" begin="0" end="3600" number="664" from="n2i" to="s4o" color="0,1,0"/>
        <flow id="SN2" begin="0" end="3600" number="285" from="s4i" to="n2o" color="0,1,0"/>

        """, file=routes)

        print("</routes>", file=routes)


def run():
    edges = set(traci.edge.getIDList())
    tls = traci.trafficlight.getIDList()

    """execute the TraCI control loop"""
    step = 1

    L = 4  # lost time because 2*4
    fixed_flow = 1850
    north_flow = [463, 463, 664, 664]
    south_flow = [586, 586, 285, 285]
    east_flow = [836, 576, 836, 576]
    west_flow = [404, 666, 404, 666]

    for tl in range(len(tls)):
        sat_north = north_flow[tl] / fixed_flow
        sat_south = south_flow[tl] / fixed_flow
        sat_east = east_flow[tl] / fixed_flow
        sat_west = west_flow[tl] / fixed_flow

        maxOfNS = max(sat_north, sat_south, 0.01)
        maxOfEW = max(sat_east, sat_west, 0.01)
        sumOfAllSats = maxOfNS + maxOfEW
        d = (1.5 * L + 5) / (1 - sumOfAllSats)  # circuit time
        GNS = (maxOfNS / sumOfAllSats) * (d - L)
        GEW = (maxOfEW / sumOfAllSats) * (d - L)

        traci.trafficlight.setPhase(tls[tl], 2)
        traci.trafficlight.setPhaseDuration(tls[tl], GEW)
        traci.trafficlight.setPhase(tls[tl], 0)
        traci.trafficlight.setPhaseDuration(tls[tl], GNS)

    total_vehs = 0
    vehs = {}
    for e in edges:
        vehs[e] = set()

    sumWait = 0
    total_vehs = 0

    # we start with phase 2 where EW has green
    while traci.simulation.getMinExpectedNumber() > 0 and step <= MAX_STEP:
        for e in edges:
            vehsNow = traci.edge.getLastStepVehicleIDs(e)
            for id in vehsNow:
                sumWait += traci.vehicle.getWaitingTime(id)
                total_vehs += 1
        traci.simulationStep()
        step += 1

    print(total_vehs)
    print(sumWait)
    print("The total waiting time of vehicles: " + str(sumWait / total_vehs))
    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
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

    # first, generate the route file for this simulation
    generate_routefile()

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start([sumoBinary, "-c", "data/cross2x2.sumocfg",
                 "--tripinfo-output", "tripinfo.xml"])
    run()
