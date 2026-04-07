from datetime import datetime
from pydantic import BaseModel

class EthicsEvent(BaseModel):
    id: str
    severity: str
    event_type: str
    description: str | None
    raw_input: str | None
    created_at: datetime
