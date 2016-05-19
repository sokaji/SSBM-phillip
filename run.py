#!/usr/bin/env python3
import time
from dolphin import runDolphin
from argparse import ArgumentParser
from multiprocessing import Process
import random
import os

# don't use gpu
# TODO: set this in tensorflow
os.environ["CUDA_VISIBLE_DEVICES"] = ""

parser = ArgumentParser()

parser.add_argument("--model", choices=["DQN", "ActorCritic"], required=True, help="which RL model to use")

#parser.add_argument("--policy", choices=["eps-greedy", "softmax"

parser.add_argument("--path", type=str,
                    help="where to import from and save to")

parser.add_argument("--tag", type=str,
                    help="optional tag to mark experiences")

parser.add_argument("--nodump", dest='dump', action="store_false",
                    help="don't dump experiences to disk")

parser.add_argument("--dump_max", type=int,
                   help="caps number of experiences")

parser.add_argument("--dolphin_dir", type=str,
                   help="dolphin user directory")

parser.add_argument("--dolphin", action="store_true", help="run dolphin")

parser.add_argument("--parallel", type=int, help="spawn parallel cpus and dolphins")

parser.add_argument("--self_play", action="store_true", help="train against ourselves")

# some duplication going on here...
#parser.add_argument("--dolphin", action="store_true", help="run dolphin")
parser.add_argument("--movie", type=str, help="movie to play on dolphin startup")
parser.add_argument("--gfx", type=str, help="gfx backend")
parser.add_argument("--exe", type=str, default="dolphin-emu-headless", help="dolphin executable")

args = parser.parse_args()

if args.path is None:
  args.path = "saves/%s/" % args.model

from cpu import CPU
def runCPU(args):
  CPU(**args).run()

if args.parallel is None:
  runCPU(args.__dict__)
else:
  prefix = args.dolphin_dir
  if prefix is None:
    prefix = 'parallel'
  
  tags = [random.getrandbits(32) for _ in range(args.parallel)]
  
  users = ['%s/%d/' % (prefix, t) for t in tags]
  cpus = []
  
  for tag, user in zip(tags, users):
    d = args.__dict__.copy()
    d['tag'] = tag
    d['dolphin_dir'] = user
    runner = Process(target=runCPU, args=[d])
    runner.start()
    cpus.append(runner)
  
  # give the runners some time to create the dolphin user directories
  time.sleep(5)
  
  dolphins = [runDolphin(user=u, **args.__dict__) for u in users]

  try:
    for c, d in zip(cpus, dolphins):
      c.join()
      d.wait()
  except KeyboardInterrupt:
    for c, d in zip(cpus, dolphins):
      c.terminate()
      d.terminate()

