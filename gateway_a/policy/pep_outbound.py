from dataclasses import dataclass
from typing import List, Tuple, Optional, Set
import logging
from qstie_common.enums.protocol_enums import TlpMarking

logger = logging.getLogger(__name__)

@dataclass
class SharingPolicyRule:
    tlp_marking: TlpMarking
    allowed_recipients: Set[str]

class OutboundPep:
    def __init__(self, policy_table: List[SharingPolicyRule]):
        self.policy_table = {rule.tlp_marking: rule.allowed_recipients for rule in policy_table}
        logger.info(f"Initialized Outbound PEP with {len(self.policy_table)} rules")

    def authorize(self, tlp: TlpMarking, recipient_id: str) -> Tuple[bool, Optional[str]]:
        """Returns (True, None) if permitted, else (False, reason_code)."""
        allowed_recipients = self.policy_table.get(tlp)
        
        if allowed_recipients is None:
            logger.warning(f"No policy defined for TLP marking: {tlp}. Failing closed.")
            return False, "POLICY_DENIED_UNKNOWN_TLP"
            
        if recipient_id not in allowed_recipients:
            logger.warning(f"Recipient {recipient_id} not authorized for TLP marking {tlp}")
            return False, "POLICY_DENIED_UNAUTHORIZED_RECIPIENT"
            
        return True, None
