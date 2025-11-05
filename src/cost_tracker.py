"""
Cost Tracking System
"""

from dataclasses import dataclass
from typing import List
import time

@dataclass
class CostRecord:
    provider: str
    characters: int
    cost: float
    timestamp: float

class CostTracker:
    RATES = {
        'inworld': 0.15,
        'openai': 0.015
    }
    
    def __init__(self):
        self.records: List[CostRecord] = []
        self.total_cost = 0.0
        self.total_characters = 0
    
    def track(self, provider: str, text: str):
        chars = len(text)
        cost = self.calculate_cost(provider, chars)
        
        self.records.append(CostRecord(
            provider=provider,
            characters=chars,
            cost=cost,
            timestamp=time.time()
        ))
        
        self.total_cost += cost
        self.total_characters += chars
    
    def calculate_cost(self, provider: str, characters: int) -> float:
        rate = self.RATES.get(provider, 0.20)
        return (characters / 1000) * rate
    
    def get_summary(self) -> dict:
        return {
            'total_cost': round(self.total_cost, 2),
            'total_characters': self.total_characters,
            'total_requests': len(self.records)
        }
