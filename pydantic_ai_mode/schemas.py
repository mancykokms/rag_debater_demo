from pydantic import BaseModel
from typing import Dict, List

class JudgeFeedback(BaseModel):
    role_specific_score: Dict[str, int]
    unaddressed_points: List[str]
    fallacies_or_gaps: List[str]
    strengths: List[str]
    summary_feedback: str
    
    
    