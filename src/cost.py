import pandas as pd
from .observations import ObservationStore

class Cost:
    """
    Calculate cost of each observation for the cost weighted optimisation
    - Each DFT calculation is a cost of 1
    - Each new motif needs to be relaxed, so the cost += 1
    - Fully analysing a motif requires a calculation for each adsorbate on all sites
    """
    def __init__(self, calculations_df: pd.DataFrame):
        self.full_df = calculations_df

    def full_motif_analysis(self, motif_id: int) -> int:
        """Full analysis of a motif requires a calculation for each adsorbate on all sites. Assumes the motif has not been relaxed"""
        calcs = self.full_df[self.full_df["motif_id"] == motif_id]
        return len(calcs) + 1
    
    def specific_adsorbate_all_sites(self, motif_id: int, adsorbate: str, observations: ObservationStore):
        """Cost of evaluating all sites for one adsorbate, including relaxation if needed."""
        calcs = self.full_df[
            (self.full_df["motif_id"] == motif_id) &
            (self.full_df["adsorbate"] == adsorbate)
        ]
        to_calculate = len(calcs)
        if motif_id in observations.observations["motif_id"].values:
            # dont need to relax bare slab, only do adsorbate calculations
            return to_calculate
        else:
            return to_calculate + 1
        
    def specific_site_and_adsorbate(self, motif_id: int, adsorbate: str, site_id: int, observations: ObservationStore):
        """Calculate the cost of calculating a specific adsorbate on a specific site of a motif, including bare slab relaxation if needed"""
        if motif_id in observations.observations["motif_id"].values:
            # dont need to relax bare slab, only do adsorbate calculations
            return 1
        else:
            return 2