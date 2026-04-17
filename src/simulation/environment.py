import time
from typing import Dict, Any, Tuple
from src.simulation.synthetic.human.py import SyntheticHuman # Wait, I need to check the exact path I used
# I'll use relative imports or ensure names match.
from src.simulation.synthetic.human import SyntheticHuman
from src.simulation.sensors.mock_perception import SensorSimulator

class SimulationEnvironment:
    """
    Closed-loop Social Interaction Environment.
    Coordinates human behavior, sensors, agent responses, and reward computation.
    """
    def __init__(self, agent: Any):
        self.agent = agent
        self.human = SyntheticHuman(mode="HYBRID")
        self.sensors = SensorSimulator(noise_level=0.01)
        self.episode_count = 0

    def step(self) -> Tuple[Dict[str, Any], Dict[str, Any], float]:
        """
        Executes a single simulation step.
        Returns (SensorData, AgentAction, Reward).
        """
        # 1. Generate Human Ground-Truth
        human_state = self.human.generate_behavior()
        
        # 2. Convert to Sensor Observation
        observation = self.sensors.capture(human_state)
        
        # 3. Agent Decides (AI Stack)
        # Agent here is expected to be the RLAgentWrapper
        action = self.agent.act(observation)
        
        # 4. Compute Social Reward
        reward = self._calculate_reward(human_state, action)
        
        return observation, action, reward

    def _calculate_reward(self, human: Dict[str, Any], action: Dict[str, Any]) -> float:
        """
        Social Alignment Reward Function.
        Rewards correct intent matching and stable emotional resonance.
        """
        reward = 0.0
        
        # 1. Intent Match (High weight)
        if human["intent"] == action.get("intent"):
            reward += 1.0
        else:
            reward -= 0.5 # Penalty for social mismatch
            
        # 2. Engagement Resonance
        # If human is highly engaged, robot should be active
        e_diff = abs(human["engagement"] - action.get("engagement", 0.5))
        reward += (0.2 - e_diff) # Positive if engagement is similar
        
        return reward
