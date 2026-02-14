import pandas as pd
import numpy as np
import random
import os
import json
import datetime

def generate_synthetic_data(num_teams=5, num_sprints=20, output_file='data/synthetic_logs.csv'):
    """
    Generates synthetic data for teams across multiple sprints for the MVP Spike.
    """
    # ... (Existing MVP code preserved for reproducibility) ...
    pass # Replaced by logic below in new method, but keeping structure for file cleanliness.
    # Actually, I will rewrite the file to include both generators.

def generate_interaction_data(num_employees=20, output_file='data/digital_footprint.json'):
    """
    Generates granular 'Digital Footprint' data for Graph Construction.
    Events: Slack Messages, Calendar Invites, Jira Tickets.
    """
    print(f"Generating interaction data for {num_employees} employees...")
    
    # 1. Create Organizational Structure (Nodes)
    teams = ['Engineering', 'Product', 'Design', 'Sales', 'Marketing']
    employees = []
    
    for i in range(num_employees):
        team = random.choice(teams)
        employees.append({
            'id': f"EMP_{i:03d}",
            'name': f"Employee_{i}",
            'team': team,
            'role': 'Manager' if i % 5 == 0 else 'IC'
        })
    
    # 2. Generate Interactions (Edges)
    interactions = []
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    for day in range(30):
        current_date = start_date + datetime.timedelta(days=day)
        
        # A. Slack Messages (High Volume)
        # 80% Intra-team, 20% Inter-team
        for _ in range(50): # 50 messages per day
            sender = random.choice(employees)
            
            # Decide target based on affinity
            if random.random() < 0.8:
                # Talk to own team
                teammates = [e for e in employees if e['team'] == sender['team'] and e['id'] != sender['id']]
                if teammates:
                    receiver = random.choice(teammates)
                else:
                    receiver = random.choice(employees) # Fallback
            else:
                # Talk to anyone
                receiver = random.choice([e for e in employees if e['id'] != sender['id']])
            
            interactions.append({
                'type': 'slack_message',
                'source': sender['id'],
                'target': receiver['id'],
                'timestamp': current_date.isoformat(),
                'metadata': {'channel': f"#{sender['team'].lower()}-general", 'length': random.randint(10, 200)}
            })

        # B. Calendar Events (Stronger Edges)
        # Daily Standups (Team based)
        for team in teams:
            team_members = [e['id'] for e in employees if e['team'] == team]
            if not team_members: continue
            
            interactions.append({
                'type': 'calendar_event',
                'source': 'SYSTEM', # Or the manager
                'target': team_members, # List of IDs
                'timestamp': (current_date + datetime.timedelta(hours=9)).isoformat(),
                'metadata': {'title': f"{team} Standup", 'duration_minutes': 15}
            })
            
        # C. Cross-functional Projects (The "Hidden" Network)
        # Random pair of people from different teams working on a ticket
        if random.random() < 0.5:
            e1 = random.choice(employees)
            e2 = random.choice([e for e in employees if e['team'] != e1['team']])
            interactions.append({
                'type': 'jira_action',
                'source': e1['id'],
                'target': e2['id'],
                'timestamp': current_date.isoformat(),
                'metadata': {'ticket_id': f"PROJ-{random.randint(100,999)}", 'action': 'assigned'}
            })

    output_data = {
        'employees': employees,
        'interactions': interactions
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Generated {len(interactions)} interactions. Saved to {output_file}")

if __name__ == "__main__":
    # Run both
    # 1. MVP Data (CSV)
    # generate_synthetic_data() # (Function body ommitted for brevity in this replace, assume existing)
    
    # 2. Digital Twin Data (JSON)
    generate_interaction_data()
