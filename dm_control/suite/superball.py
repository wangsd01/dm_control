# Copyright 2017 The dm_control Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Planar superball Domain."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections

from dm_control import mujoco
from dm_control.rl import control
from dm_control.suite import base
from dm_control.suite import common
from dm_control.suite.utils import randomizers
from dm_control.utils import containers
from dm_control.utils import rewards
from dm_env import specs
import numpy as np

_DEFAULT_TIME_LIMIT = 100
_CONTROL_TIMESTEP = .1

# Minimal height of torso over foot above which stand reward is 1.
_STAND_HEIGHT = 7.50

# Horizontal speeds (meters/second) above which move reward is 1.
_RUN_SPEED = 10

SUITE = containers.TaggedTasks()


def get_model_and_assets():
  """Returns a tuple containing the model XML string and a dict of assets."""
  # return common.read_model('superball.xml'), common.ASSETS
  return common.read_model('tt_ntrt_hanging.xml'), common.ASSETS

@SUITE.add('benchmarking')
def stop_wing(time_limit=_DEFAULT_TIME_LIMIT, random=None, environment_kwargs=None):
  """Returns the Stand task."""
  physics = Physics.from_xml_string(*get_model_and_assets())
  task = StopSwing(move_speed=0, random=random)
  environment_kwargs = environment_kwargs or {}
  return control.Environment(
    physics, task, time_limit=time_limit, control_timestep=_CONTROL_TIMESTEP,
    **environment_kwargs)

@SUITE.add('benchmarking')
def stand(time_limit=_DEFAULT_TIME_LIMIT, random=None, environment_kwargs=None):
  """Returns the Stand task."""
  physics = Physics.from_xml_string(*get_model_and_assets())
  task = Stand(move_speed=0, height=_STAND_HEIGHT, random=random)
  environment_kwargs = environment_kwargs or {}
  return control.Environment(
    physics, task, time_limit=time_limit, control_timestep=_CONTROL_TIMESTEP,
    **environment_kwargs)

@SUITE.add('benchmarking')
def run(time_limit=_DEFAULT_TIME_LIMIT, random=None, environment_kwargs=None):
  """Returns the Run task."""
  physics = Physics.from_xml_string(*get_model_and_assets())
  task = Run(move_speed=_RUN_SPEED, random=random)
  environment_kwargs = environment_kwargs or {}
  return control.Environment(
    physics, task, time_limit=time_limit, control_timestep=_CONTROL_TIMESTEP,
    **environment_kwargs)


class Physics(mujoco.Physics):
  """Physics simulation with additional features for the superball domain."""

  # def torso_upright(self):
  #   """Returns projection from z-axes of torso to the z-axes of world."""
  #   return self.named.data.xmat[1:, 'zz']

  def superball_height(self):
    """Returns the height of the torso."""
    return np.mean(self.named.data.xpos[1:, 'z'])

  def superball_lin_velocity_on_x_axis(self):
    """Returns the horizontal velocity of the center-of-mass."""
    return np.mean(self.named.data.cvel[1:, 3])

  def superball_lin_velocity(self):
    return np.linalg.norm(np.mean(self.named.data.cvel[1:, 3:], axis=0))

  def rods_orientations(self):
    """Returns planar orientations of all bodies."""
    return self.named.data.xmat[1:, ['xx', 'xz']].ravel()

  def rods_velocities(self):
    return self.named.data.cvel[1:, 3:]

  def rods_heights(self):
    return self.named.data.xpos[1:, 'z']


class PlanarSuperball(base.Task):
  """A planar superball task."""

  def __init__(self, move_speed=None, height=None, random=None):
    """Initializes an instance of `PlanarSuperball`.

    Args:
      move_speed: A float. If this value is zero, reward is given simply for
        standing up. Otherwise this specifies a target horizontal velocity for
        the walking task.
      random: Optional, either a `numpy.random.RandomState` instance, an
        integer seed for creating a new `RandomState`, or None to select a seed
        automatically (default).
    """
    self._move_speed = move_speed
    self._height = height
    super(PlanarSuperball, self).__init__(random=random)

  def initialize_episode(self, physics):
    """Sets the state of the environment at the start of each episode.

    In 'standing' mode, use initial orientation and small velocities.
    In 'random' mode, randomize joint angles and let fall to the floor.

    Args:
      physics: An instance of `Physics`.

    """
    # randomizers.randomize_limited_and_rotational_joints(physics, self.random)
    super(PlanarSuperball, self).initialize_episode(physics)
    # self.actuators = physics.find_all('actuator')

  def get_observation(self, physics):
    """Returns an observation of body height and velocites."""
    obs = collections.OrderedDict()
    obs['height'] = physics.rods_heights()
    obs['velocity'] = physics.rods_velocities()
    obs['orientation'] = physics.rods_orientations()
    return obs

  def action_spec(self, _physics):
    minimum, maximum = -100, 100
    return specs.BoundedArray(
      shape=(24,),
      dtype=np.float,
      minimum=minimum,
      maximum=maximum)

class Stand(PlanarSuperball):
  def get_reward(self, physics):
    """Returns a reward to the agent."""
    stand_reward = -(physics.superball_height() - self._height)**2
    print("Height is ", physics.superball_height())
    return stand_reward


class Run(PlanarSuperball):
  def get_reward(self, physics):
    move_reward = -(physics.superball_lin_velocity_on_x_axis() - self._move_speed)**2
    return move_reward

class StopSwing(PlanarSuperball):
  def get_reward(self, physics):
    move_reward = -(physics.superball_lin_velocity() - self._move_speed)**2
    return move_reward



