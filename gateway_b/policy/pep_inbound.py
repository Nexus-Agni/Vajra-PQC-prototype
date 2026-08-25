import logging

class InboundPEP:
    def __init__(self, rules=None):
        # A simple ruleset for prototype
        # Each rule: {'sender': '...', 'recipient': '...', 'tlp': '...', 'action': 'ALLOW' | 'DENY'}
        self.rules = rules or []

    def evaluate(self, sender_id: str, recipient_id: str, tlp_marking: str) -> tuple[bool, str]:
        # Exact match rules
        # First match wins (like a simple firewall)
        for rule in self.rules:
            s_match = (rule.get('sender') == '*' or rule.get('sender') == sender_id)
            r_match = (rule.get('recipient') == '*' or rule.get('recipient') == recipient_id)
            t_match = (rule.get('tlp') == '*' or rule.get('tlp') == tlp_marking)
            
            if s_match and r_match and t_match:
                if rule.get('action') == 'DENY':
                    return False, f"Explicit DENY rule matched"
                elif rule.get('action') == 'ALLOW':
                    return True, f"Explicit ALLOW rule matched"
                    
        return False, "Policy rule not found"
