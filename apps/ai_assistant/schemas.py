from typing import List, Optional, TypedDict

class StepSchema(TypedDict):
    number: int
    text: str
    url: Optional[str]

class GuideResponseSchema(TypedDict):
    status: str  # ok, needs_review, cannot_answer, error
    title: str
    answer: str
    steps: List[StepSchema]
    warnings: List[str]
    sources: List[str]
    requires_human_review: bool
