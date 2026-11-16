import pandas as pd

class ObservationStore:
    def __init__(self):
        self.observations = pd.DataFrame(columns=[
            "iteration", "calculation_id", "motif_id",
            "adsorbate", "site_id", "energy_eV", "cost"
        ])
        self.observations = self.observations.astype({
            "iteration": "int64",
            "calculation_id": "int64",
            "motif_id": "int64",
            "site_id": "int64",
            "energy_eV": "float64",
            "cost": "int64"
        })
    


    def add(self, results, iteration):
        results = results.copy()
        results["iteration"] = iteration

        existing = set(self.observations["calculation_id"])
        results = results[~results["calculation_id"].isin(existing)]

        self.observations = pd.concat(
            [self.observations, results],
            ignore_index=True
        )

    @property
    def total_cost(self):
        return self.observations["cost"].sum()

    def evaluated_calculations(self):
        return set(self.observations["calculation_id"])

    def save(self, path):
        self.observations.to_csv(path, index=False)