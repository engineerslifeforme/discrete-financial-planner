from dataclasses import dataclass, asdict

@dataclass
class Action:
    amount: float    
    asset_name: str
    fed_taxable: bool = False
    fed_tax_payment: bool = False
    fed_tax_deductible: bool = False
    description: str = "Default Description"
    category: str = "Default"
    priority: int = 200

    def dict(self):
        return {k: str(v) for k, v in asdict(self).items()}
