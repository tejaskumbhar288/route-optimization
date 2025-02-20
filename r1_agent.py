import random
import numpy as np

class R1Agent:
    def __init__(self, start, end, learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0):
        self.start = start
        self.end = end
        self.learning_rate = learning_rate  # How much to update Q-values
        self.discount_factor = discount_factor  # How much to discount future rewards
        self.exploration_rate = exploration_rate  # Probability of exploring instead of exploiting
        self.q_table = {}  # To store Q-values (state, action) -> reward
        
        self.routes = self.get_available_routes()

    def get_available_routes(self):
        """
        Simulate fetching multiple routes from a mapping API (e.g., Google Maps).
        For simplicity, we're assuming 3 possible routes with random data for distance, duration, and traffic delays.
        """
        routes = []
        
        # Simulate routes with random data for demonstration
        for i in range(3):
            route = {
                'route_id': i,
                'distance': random.randint(5, 20),  # in kilometers
                'duration': random.randint(10, 60),  # in minutes
                'traffic_delay': random.randint(0, 1000)  # random traffic delay in seconds
            }
            routes.append(route)
        
        return routes

    def reward_function(self, route):
        """
        Define the reward function based on the route characteristics.
        Here, shorter duration and lower traffic delay will result in higher rewards.
        """
        reward = -route['duration'] - route['traffic_delay']  # Negative for penalty
        return reward

    def get_state(self):
        """
        The state could include various factors like current traffic conditions,
        the time of day, and historical data (for simplicity, we use only route data).
        """
        state = tuple([route['route_id'] for route in self.routes])  # State as a tuple of route_ids
        return state

    def choose_action(self, state):
        """
        Epsilon-greedy approach: Choose the best known action (exploitation) or explore a random one.
        """
        if random.uniform(0, 1) < self.exploration_rate:
            # Exploration: Choose a random route
            return random.choice(self.routes)
        else:
            # Exploitation: Choose the route with the highest Q-value (best known action)
            if state not in self.q_table:
                self.q_table[state] = np.zeros(len(self.routes))  # Initialize Q-values for the state
            return self.routes[np.argmax(self.q_table[state])]

    def update_q_table(self, state, action, reward, next_state):
        """
        Update Q-value using the Q-learning formula:
        Q(s, a) = Q(s, a) + alpha * (reward + gamma * max_a Q(s', a) - Q(s, a))
        """
        if state not in self.q_table:
            self.q_table[state] = np.zeros(len(self.routes))
        
        if next_state not in self.q_table:
            self.q_table[next_state] = np.zeros(len(self.routes))
        
        best_future_q = np.max(self.q_table[next_state])  # Best Q-value for next state (future reward)
        current_q = self.q_table[state][action['route_id']]  # Current Q-value for the selected action
        
        # Update Q-value for the selected action
        self.q_table[state][action['route_id']] = current_q + self.learning_rate * (reward + self.discount_factor * best_future_q - current_q)

    def train(self, episodes=1000):
        """
        Train the agent by interacting with the environment.
        """
        for episode in range(episodes):
            state = self.get_state()  # Get the initial state
            action = self.choose_action(state)  # Choose an action (route)
            reward = self.reward_function(action)  # Get the reward for that action
            next_state = self.get_state()  # In this simple case, the state doesn't change
            
            # Update Q-values based on the action taken
            self.update_q_table(state, action, reward, next_state)
            
            # Optionally, reduce exploration over time to favor exploitation
            self.exploration_rate = max(0.1, self.exploration_rate * 0.99)
    
    def get_optimal_route(self):
        """
        After training, the agent selects the best route.
        """
        state = self.get_state()
        action = self.choose_action(state)  # Choose the best action
        return {
            'route_id': action['route_id'],
            'distance': action['distance'],
            'duration': action['duration'],
            'estimated_cost': action['distance'] * 0.1  # Estimated cost
        }

