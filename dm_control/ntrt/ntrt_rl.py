from dm_control import suite
import numpy as np

# Load one task:
env = suite.load(domain_name="superball", task_name="stop_wing")

# Iterate over a task set:
# for domain_name, task_name in suite.BENCHMARKING:
#   env = suite.load(domain_name, task_name)

# Step through an episode and print out reward, discount and observation.
action_spec = env.action_spec()
time_step = env.reset()
while not time_step.last():
  # action = np.random.uniform(action_spec.minimum,
  #                            action_spec.maximum,
  #                            size=action_spec.shape)
  action = np.random.uniform(0,
                             0,
                             size=action_spec.shape)
  time_step = env.step(action)
  # print(time_step.reward, time_step.discount, time_step.observation)