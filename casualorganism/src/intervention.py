import datetime

class MockAPI:
    """
    Simulates external APIs (Slack, Calendar, Jira)
    """
    def __init__(self):
        self.logs = []

    def post_slack_message(self, user_id, message):
        log = f"[SLACK] To {user_id}: {message}"
        self.logs.append(log)
        print(log)
        return True

    def schedule_calendar_event(self, user_ids, title, time, duration_mins):
        log = f"[CALENDAR] Scheduled '{title}' for {user_ids} at {time} ({duration_mins}m)"
        self.logs.append(log)
        print(log)
        return True

    def modify_role_permissions(self, user_id, new_role):
        log = f"[HR_SYSTEM] Promoted {user_id} to {new_role}"
        self.logs.append(log)
        print(log)
        return True


class ActionOrchestrator:
    def __init__(self, mode='shadow'):
        """
        mode: 
          - 'shadow': Log actions but do not execute (Safe).
          - 'live': Execute actions against APIs.
        """
        self.mode = mode
        self.api = MockAPI()
        print(f"Orchestrator initialized in {self.mode.upper()} mode.")

    def validate_safety(self, action_type, params):
        """
        Constitutional AI / Safety Layer.
        Returns True if action is safe to execute.
        """
        # Rule 1: Do not fire people automatically.
        if action_type == 'fire_employee':
            print("SAFETY WARNING: Action 'fire_employee' rejected by safety policy.")
            return False
            
        # Rule 2: Do not cancel more than 3 meetings at once (Mass disruption).
        if action_type == 'cancel_meeting_batch' and len(params.get('meeting_ids', [])) > 3:
            print("SAFETY WARNING: Batch cancellation > 3 rejected.")
            return False

        return True

    def execute_intervention(self, intervention_plan):
        """
        Takes a plan (list of actions) and executes them.
        intervention_plan = [
            {'action': 'schedule_focus_time', 'target': 'EMP_002', 'params': {...}},
            ...
        ]
        """
        print("\n--- Executing Intervention Plan ---")
        for step in intervention_plan:
            action = step['action']
            target = step['target']
            params = step.get('params', {})
            
            # 1. Safety Check
            if not self.validate_safety(action, params):
                print(f"Skipping unsafe action: {action}")
                continue
                
            # 2. Execution (or Shadow Log)
            if self.mode == 'shadow':
                print(f"[SHADOW] Would execute: {action} on {target} with {params}")
            elif self.mode == 'live':
                self._dispatch_to_api(action, target, params)

    def _dispatch_to_api(self, action, target, params):
        if action == 'schedule_focus_time':
            # Schedule 2 hours of Deep Work tomorrow at 9am
            tomorrow_9am = datetime.datetime.now() + datetime.timedelta(days=1)
            tomorrow_9am = tomorrow_9am.replace(hour=9, minute=0, second=0)
            self.api.schedule_calendar_event(
                [target], 
                "Deep Work (Causal Optimizer)", 
                tomorrow_9am.isoformat(), 
                120
            )
            # Notify user
            self.api.post_slack_message(
                target, 
                "Hi! I've scheduled Deep Work for you tomorrow to protect your maker time."
            )
            
        elif action == 'promote_role':
            new_role = params.get('new_role', 'Manager')
            self.api.modify_role_permissions(target, new_role)
            self.api.post_slack_message(
                target, 
                f"Congratulations! You have been promoted to {new_role} to better support your team."
            )

if __name__ == "__main__":
    # Test Driver
    orchestrator = ActionOrchestrator(mode='live')
    
    # 1. Test Safety Rejection
    orchestrator.execute_intervention([
        {'action': 'fire_employee', 'target': 'EMP_666'} 
    ])
    
    # 2. Test Safe Execution (Scenario: Fix Burnout for Employee_2)
    orchestrator.execute_intervention([
        {
            'action': 'schedule_focus_time', 
            'target': 'EMP_002', 
            'params': {'duration': 120}
        }
    ])
