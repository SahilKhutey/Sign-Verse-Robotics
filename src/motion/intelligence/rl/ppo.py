import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, List, Tuple
from src.motion.intelligence.rl.models import ActorNetwork, CriticNetwork

class PPOAgent:
    """
    Proximal Policy Optimization (PPO) Agent for HRI Social Policies.
    Stable on-policy reinforcement learning for discrete actions.
    """
    def __init__(self, config: Dict[str, Any]):
        self.state_dim = config["environment"]["state_dim"]
        self.action_dim = config["environment"]["action_dim"]
        self.lr = config["ppo"]["learning_rate"]
        self.gamma = config["ppo"]["gamma"]
        self.eps_clip = config["ppo"]["epsilon_clip"]
        self.entropy_beta = config["ppo"]["entropy_beta"]
        
        # Networks
        self.actor = ActorNetwork(self.state_dim, self.action_dim)
        self.critic = CriticNetwork(self.state_dim)
        
        self.optimizer = optim.Adam([
            {'params': self.actor.parameters(), 'lr': self.lr},
            {'params': self.critic.parameters(), 'lr': self.lr}
        ])
        
        self.MseLoss = nn.MSELoss()

    def select_action(self, state: torch.Tensor, stochastic: bool = True) -> Tuple[int, torch.Tensor]:
        """
        Samples an action from the policy distribution.
        """
        probs = self.actor(state)
        
        if stochastic:
            dist = torch.distributions.Categorical(probs)
            action = dist.sample()
            return action.item(), dist.log_prob(action)
        else:
            # Deterministic/Greedy selection
            action = torch.argmax(probs)
            return action.item(), torch.log(probs[action] + 1e-8)

    def update(self, buffer: List[Tuple[torch.Tensor, int, torch.Tensor, float, bool]]):
        """
        Executes PPO policy update over a batch of trajectories.
        """
        # 1. Unpack buffer
        states = torch.stack([t[0] for t in buffer])
        actions = torch.tensor([t[1] for t in buffer])
        old_log_probs = torch.stack([t[2] for t in buffer]).detach()
        rewards = torch.tensor([t[3] for t in buffer])
        
        # 2. Compute Target Values and Advantages
        with torch.no_grad():
            values = self.critic(states).squeeze(-1)
            # Simplified Advantage: Reward - Value
            advantages = rewards - values
            
        # 3. PPO Update Logic
        for _ in range(5): # Multiple epochs
            # Re-evaluate current policy
            new_probs = self.actor(states)
            dist = torch.distributions.Categorical(new_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()
            
            # Policy Ratio
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # Clipped Surrogate Objective
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantages
            
            policy_loss = -torch.min(surr1, surr2).mean() - self.entropy_beta * entropy
            
            # Value Loss
            current_values = self.critic(states).squeeze(-1)
            value_loss = self.MseLoss(current_values, rewards)
            
            # Backprop
            self.optimizer.zero_grad()
            (policy_loss + 0.5 * value_loss).backward()
            self.optimizer.step()
            
    def save(self, path: str):
        torch.save({
            'actor': self.actor.state_dict(),
            'critic': self.critic.state_dict()
        }, path)

    def load(self, path: str):
        checkpoint = torch.load(path, map_location='cpu')
        self.actor.load_state_dict(checkpoint['actor'])
        self.critic.load_state_dict(checkpoint['critic'])
