"""
SaaSQuatch Acquisition Intelligence Engine
Transforms basic lead data into actionable acquisition opportunities
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import json

class AcquisitionScorer:
    """
    Scores businesses based on acquisition potential, not just sales potential
    Focuses on owner readiness, financial health, and deal viability
    """
    
    def __init__(self):
        # Weights optimized for acquisition success
        self.weights = {
            'owner_readiness': 0.30,      # Most important - willing seller
            'financial_health': 0.25,     # Profitability and stability
            'valuation_reason': 0.20,     # Price expectations
            'business_quality': 0.15,     # Defensible position
            'transition_ease': 0.10       # How smooth the handoff will be
        }
    
    def score_target(self, company: Dict) -> Tuple[int, List[Dict]]:
        """
        Score a potential acquisition target
        Returns: (score 0-100, list of signals)
        """
        signals = []
        component_scores = {}
        
        # 1. Owner Readiness Score (30%)
        owner_score, owner_signals = self._score_owner_readiness(company)
        component_scores['owner_readiness'] = owner_score
        signals.extend(owner_signals)
        
        # 2. Financial Health Score (25%)
        financial_score, financial_signals = self._score_financial_health(company)
        component_scores['financial_health'] = financial_score
        signals.extend(financial_signals)
        
        # 3. Valuation Reasonableness (20%)
        valuation_score, valuation_signals = self._score_valuation(company)
        component_scores['valuation_reason'] = valuation_score
        signals.extend(valuation_signals)
        
        # 4. Business Quality (15%)
        quality_score, quality_signals = self._score_business_quality(company)
        component_scores['business_quality'] = quality_score
        signals.extend(quality_signals)
        
        # 5. Transition Ease (10%)
        transition_score, transition_signals = self._score_transition_ease(company)
        component_scores['transition_ease'] = transition_score
        signals.extend(transition_signals)
        
        # Calculate weighted total
        total_score = sum(
            component_scores[key] * self.weights[key] * 100
            for key in self.weights
        )
        
        return int(total_score), signals
    
    def _score_owner_readiness(self, company: Dict) -> Tuple[float, List[Dict]]:
        """Evaluate how ready the owner is to sell"""
        score = 0
        signals = []
        
        owner_age = company.get('owner_age', 0)
        if owner_age >= 60:
            score += 0.5
            signals.append({
                'type': 'positive',
                'text': f'Owner approaching retirement age ({owner_age})'
            })
        elif owner_age >= 55:
            score += 0.3
            signals.append({
                'type': 'neutral',
                'text': f'Owner age {owner_age} - may consider exit in 5 years'
            })
        elif owner_age < 45:
            signals.append({
                'type': 'warning',
                'text': f'Young owner ({owner_age}) - less likely to sell'
            })
        
        # Check for other readiness indicators
        if company.get('actively_selling', False):
            score += 0.3
            signals.append({
                'type': 'positive',
                'text': 'Business actively listed for sale'
            })
        
        if company.get('years_owned', 0) > 10:
            score += 0.2
            signals.append({
                'type': 'positive',
                'text': f'Long ownership tenure ({company["years_owned"]} years)'
            })
            
        return min(1.0, score), signals
    
    def _score_financial_health(self, company: Dict) -> Tuple[float, List[Dict]]:
        """Evaluate financial performance and stability"""
        score = 0
        signals = []
        
        # EBITDA margin analysis
        revenue = company.get('revenue', 0)
        ebitda = company.get('ebitda', 0)
        
        if revenue > 0:
            margin = (ebitda / revenue) * 100
            if margin >= 25:
                score += 0.4
                signals.append({
                    'type': 'positive',
                    'text': f'{margin:.1f}% EBITDA margin - highly profitable'
                })
            elif margin >= 20:
                score += 0.3
                signals.append({
                    'type': 'positive',
                    'text': f'{margin:.1f}% EBITDA margin - strong profitability'
                })
            elif margin >= 15:
                score += 0.2
                signals.append({
                    'type': 'neutral',
                    'text': f'{margin:.1f}% EBITDA margin - industry average'
                })
            elif margin < 10:
                signals.append({
                    'type': 'warning',
                    'text': f'{margin:.1f}% EBITDA margin - below average'
                })
        
        # Revenue stability
        if company.get('recurring_revenue_pct', 0) > 70:
            score += 0.3
            signals.append({
                'type': 'positive',
                'text': f'{company["recurring_revenue_pct"]}% recurring revenue'
            })
        
        # Growth rate
        growth_rate = company.get('revenue_growth_rate', 0)
        if growth_rate > 20:
            score += 0.3
            signals.append({
                'type': 'positive',
                'text': f'Consistent {growth_rate}% YoY growth'
            })
            
        return min(1.0, score), signals
    
    def _score_valuation(self, company: Dict) -> Tuple[float, List[Dict]]:
        """Evaluate if the asking price is reasonable"""
        score = 0
        signals = []
        
        ebitda = company.get('ebitda', 1)  # Avoid division by zero
        asking_price = company.get('asking_price', 0)
        
        if asking_price > 0 and ebitda > 0:
            multiple = asking_price / ebitda
            
            if multiple <= 4:
                score = 1.0
                signals.append({
                    'type': 'positive',
                    'text': f'Attractive valuation at {multiple:.1f}x EBITDA'
                })
            elif multiple <= 5:
                score = 0.7
                signals.append({
                    'type': 'neutral',
                    'text': f'Fair valuation at {multiple:.1f}x EBITDA'
                })
            elif multiple <= 6:
                score = 0.5
                signals.append({
                    'type': 'neutral',
                    'text': f'Market valuation at {multiple:.1f}x EBITDA'
                })
            else:
                score = 0.2
                signals.append({
                    'type': 'warning',
                    'text': f'High valuation at {multiple:.1f}x EBITDA'
                })
                
        return score, signals
    
    def _score_business_quality(self, company: Dict) -> Tuple[float, List[Dict]]:
        """Evaluate the quality and defensibility of the business"""
        score = 0
        signals = []
        
        # Customer concentration
        customer_concentration = company.get('top_customer_concentration', 0)
        if customer_concentration < 20:
            score += 0.3
            signals.append({
                'type': 'positive',
                'text': 'Well-diversified customer base'
            })
        elif customer_concentration > 40:
            signals.append({
                'type': 'warning',
                'text': f'High customer concentration (top 3 = {customer_concentration}%)'
            })
        
        # Business age and stability
        year_founded = company.get('year_founded', datetime.now().year)
        business_age = datetime.now().year - year_founded
        
        if business_age >= 10:
            score += 0.4
            signals.append({
                'type': 'positive',
                'text': f'Established business ({business_age} years)'
            })
        elif business_age >= 5:
            score += 0.2
        
        # Market position
        if company.get('market_leader', False):
            score += 0.3
            signals.append({
                'type': 'positive',
                'text': 'Market leader in their niche'
            })
            
        return min(1.0, score), signals
    
    def _score_transition_ease(self, company: Dict) -> Tuple[float, List[Dict]]:
        """Evaluate how easy the business will be to transition"""
        score = 0
        signals = []
        
        # Management team
        if company.get('has_management_team', False):
            score += 0.5
            signals.append({
                'type': 'positive',
                'text': 'Strong management team in place'
            })
        else:
            signals.append({
                'type': 'warning',
                'text': 'Owner-dependent business'
            })
        
        # Systems and processes
        if company.get('documented_processes', False):
            score += 0.3
            signals.append({
                'type': 'positive',
                'text': 'Well-documented processes and systems'
            })
        
        # Seller cooperation
        if company.get('seller_will_stay', False):
            score += 0.2
            signals.append({
                'type': 'positive',
                'text': 'Seller willing to stay for transition'
            })
            
        return min(1.0, score), signals

class DataEnricher:
    """
    Enriches basic company data with acquisition-relevant information
    In production, this would pull from multiple data sources
    """
    
    def enrich_company_data(self, company_name: str, website: str) -> Dict:
        """
        Enrich company data with additional acquisition signals
        In production, this would use APIs like:
        - Business broker listings (BizBuySell, BusinessesForSale)
        - Financial data providers (PitchBook, PrivCo)
        - Public records (Secretary of State filings)
        """
        
        # Simulated enrichment - in production, real API calls
        enriched_data = {
            'owner_signals': self._get_owner_signals(company_name),
            'financial_estimates': self._estimate_financials(website),
            'market_data': self._get_market_intelligence(company_name),
            'risk_factors': self._identify_risks(company_name)
        }
        
        return enriched_data
    
    def _get_owner_signals(self, company_name: str) -> Dict:
        """Find signals about owner's readiness to sell"""
        # In production: LinkedIn data, news mentions, broker listings
        return {
            'owner_age_estimate': 55,
            'succession_planning_mentioned': True,
            'recent_advisor_hires': ['Investment banker hired', 'CPA firm engaged']
        }
    
    def _estimate_financials(self, website: str) -> Dict:
        """Estimate financial metrics from various signals"""
        # In production: Use employee count, industry benchmarks, growth signals
        return {
            'estimated_revenue_range': (5000000, 10000000),
            'estimated_ebitda_margin': 0.20,
            'growth_indicators': ['Hiring rapidly', 'New office opened']
        }
    
    def _get_market_intelligence(self, company_name: str) -> Dict:
        """Gather market and competitive intelligence"""
        return {
            'industry_multiples': 4.5,
            'recent_acquisitions': ['Competitor sold for 5x EBITDA'],
            'market_trends': ['Industry consolidating', 'PE interest high']
        }
    
    def _identify_risks(self, company_name: str) -> List[str]:
        """Identify potential acquisition risks"""
        return [
            'Customer concentration risk',
            'Technology platform aging',
            'Key employee retention risk'
        ]

# Example usage and data generation
def generate_sample_data():
    """Generate realistic sample data for demonstration"""
    
    companies = [
        {
            'company_name': 'TechFlow Solutions',
            'website': 'techflowsolutions.com',
            'industry': 'SaaS',
            'location': 'Austin, TX',
            'employees': 75,
            'year_founded': 2015,
            'revenue': 8500000,
            'ebitda': 2125000,
            'owner_age': 58,
            'asking_price': 10000000,
            'recurring_revenue_pct': 85,
            'revenue_growth_rate': 25,
            'top_customer_concentration': 15,
            'has_management_team': True,
            'documented_processes': True,
            'actively_selling': True,
            'years_owned': 8,
            'seller_will_stay': True
        },
        # Add more sample companies...
    ]
    
    return companies

def main():
    """Main execution - score and rank acquisition targets"""
    
    # Initialize components
    scorer = AcquisitionScorer()
    enricher = DataEnricher()
    
    # Get sample data
    companies = generate_sample_data()
    
    # Score each company
    results = []
    for company in companies:
        # Enrich data
        enriched = enricher.enrich_company_data(
            company['company_name'], 
            company['website']
        )
        
        # Calculate score
        score, signals = scorer.score_target(company)
        
        results.append({
            'company': company,
            'score': score,
            'signals': signals,
            'enriched_data': enriched
        })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Output results
    print("Top Acquisition Targets:")
    print("-" * 50)
    
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. {result['company']['company_name']} - Score: {result['score']}")
        print(f"   Industry: {result['company']['industry']}")
        print(f"   Revenue: ${result['company']['revenue']:,.0f}")
        print(f"   Asking: ${result['company']['asking_price']:,.0f}")
        print(f"   Multiple: {result['company']['asking_price']/result['company']['ebitda']:.1f}x")
        print("\n   Key Signals:")
        for signal in result['signals'][:3]:
            print(f"   - {signal['text']}")

if __name__ == "__main__":
    main()