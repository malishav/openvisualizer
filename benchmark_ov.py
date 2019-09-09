import argparse
import subprocess
import os

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

args = parser.parse_args()

for i in range(args.numRuns):
    subprocess.call(
             ['scons', 'runweb', '--port=8082', '--testbed={0}'.format(args.testbed), '--benchmark={0}'.format(args.scenario), '--bootloadTestbed', '--opentun-null'],
#            ['scons', 'runweb', '--port=8082', '--sim', '--simCount=4', '--simTopology=linear', '--benchmark={0}'.format(args.scenario), '--opentun-null'],
            )
    # rename OV log to match the run number
    subprocess.call(
            ['mv', 'openVisualizer.log', 'openVisualizer_run_{0}.log'.format(i)],
            cwd=os.path.join(os.path.dirname(__file__), 'build', 'runui')
            )
