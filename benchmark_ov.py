import argparse
import subprocess
import os
import random

parser = argparse.ArgumentParser()

parser.add_argument('--numRuns',
        dest       = 'numRuns',
        type       = int,
        default    = 1,
        required   = False,
        action     = 'store',
        )

parser.add_argument('--testbed',
        dest       = 'testbed',
        choices    = ['iotlab', 'wilab', 'opentestbed'],
        required   = True,
        action     = 'store',
        )

parser.add_argument('--scenario',
        dest       = 'scenario',
        choices    = ['industrial-monitoring', 'home-automation', 'building-automation', 'demo-scenario'],
        required   = True,
        action     = 'store',
        )

parser.add_argument('--port',
        dest       = 'port',
        type       = int,
        default    = 0,
        required   = False,
        action     = 'store',
        )

args = parser.parse_args()

# Start at random port if --port is not provided. This allows multiple instances of OV to run on the same machine.
if args.port == 0:
        port = random.randint(49152, 65535)
else:
        port = args.port

for i in range(args.numRuns):
    subprocess.call(
             ['scons', 'runweb', '--port={0}'.format(port), '--testbed={0}'.format(args.testbed), '--benchmark={0}'.format(args.scenario), '--bootloadTestbed', '--opentun-null'],
#            ['scons', 'runweb', '--port=8082', '--sim', '--simCount=4', '--simTopology=linear', '--benchmark={0}'.format(args.scenario), '--opentun-null'],
            )
    # rename OV log to match the run number
    subprocess.call(
            ['mv', 'openVisualizer.log', 'openVisualizer_run_{0}.log'.format(i)],
            cwd=os.path.join(os.path.dirname(__file__), 'build', 'runui')
            )
