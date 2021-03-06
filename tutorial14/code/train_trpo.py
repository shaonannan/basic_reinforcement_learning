from baselines.ppo1.mlp_policy import MlpPolicy
from baselines.common.mpi_fork import mpi_fork
from baselines import bench
from baselines.trpo_mpi import trpo_mpi
import gym
import tensorflow as tf
import argparse
import baselines.common.tf_util as U
from baselines.common import set_global_seeds
from mpi4py import MPI

#parser
parser = argparse.ArgumentParser()
parser.add_argument('--environment', dest='environment', type=str, default='MountainCarContinuous-v0')
parser.add_argument('--num_timesteps', dest='num_timesteps', type=int, default=10000)
parser.add_argument('--seed', help='RNG seed', type=int, default=0)
args = parser.parse_args()

sess = U.single_threaded_session()
sess.__enter__()

rank = MPI.COMM_WORLD.Get_rank()
if rank != 0:
    logger.set_level(logger.DISABLED)
workerseed = args.seed + 10000 * MPI.COMM_WORLD.Get_rank()
set_global_seeds(workerseed)

# create the environment
env = gym.make(str(args.environment))
# initial_observation = env.reset()

def policy_fn(name, ob_space, ac_space):
    return MlpPolicy(name=name, ob_space=env.observation_space, ac_space=env.action_space,
        hid_size=32, num_hid_layers=2)
# env = bench.Monitor(env, logger.get_dir() and
#     osp.join(logger.get_dir(), str(rank)))
env.seed(workerseed)
# gym.logger.setLevel(logging.WARN)
with tf.Session() as sess:
    trpo_mpi.learn(env, policy_fn,
        timesteps_per_batch=1024,
        max_kl=0.01, cg_iters=10, cg_damping=0.1,
        max_timesteps=args.num_timesteps,
        gamma=0.99, lam=0.98, vf_iters=5, vf_stepsize=1e-3,
        save_model_with_prefix="",
        outdir="/tmp/experiments/"+str(args.environment)+"/TRPO/")
