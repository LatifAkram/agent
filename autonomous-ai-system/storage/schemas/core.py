from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AcceptanceTest(BaseModel):
	id: str
	description: str
	check_type: str
	threshold: Optional[float] = None

class AgentState(BaseModel):
	task_id: str
	requirements: Dict[str, Any]
	todo: List[Dict[str, Any]]
	artifacts: List[Dict[str, Any]]
	evidence: List[Dict[str, Any]]
	acceptance_tests: List[AcceptanceTest]
	status: str
