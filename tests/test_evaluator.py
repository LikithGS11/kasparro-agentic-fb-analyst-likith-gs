import pandas as pd
import numpy as np

class EvaluatorAgent:
    """
    EvaluatorAgent validates hypotheses using quantitative metrics.
    It supports:
    - calculate_metrics(df)
    - evaluate_hypothesis(hypothesis, metrics, df)
    - run(hypotheses, df)
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.low_ctr_thr = cfg.get("low_ctr_threshold", 0.01)
        self.low_roas_thr = cfg.get("low_roas_threshold", 1.5)
        self.min_impr = cfg.get("min_impressions", 1000)

    # -------------------------------------------------------------
    # 1️⃣ Calculate dataset-level metrics
    # -------------------------------------------------------------
    def calculate_metrics(self, df: pd.DataFrame):
        metrics = {
            "avg_roas": float(df["roas"].mean()),
            "avg_ctr": float(df["ctr"].mean()),
            "total_clicks": int(df["clicks"].sum()),
            "mean_impressions": float(df["impressions"].mean()),
            "ctr_below_threshold": float(df["ctr"].mean() < self.low_ctr_thr),
            "roas_below_threshold": float(df["roas"].mean() < self.low_roas_thr)
        }
        return metrics

    # -------------------------------------------------------------
    # 2️⃣ Evaluate a single hypothesis
    # -------------------------------------------------------------
    def evaluate_hypothesis(self, hypothesis: dict, metrics: dict, df: pd.DataFrame):
        text = hypothesis.get("hypothesis", "").lower()
        base_conf = hypothesis.get("confidence", 0.5)

        evidence = []

        calculated_conf = base_conf

        # --- Case 1: low CTR hypothesis ---------------------------------------
        if "low ctr" in text:
            avg_ctr = metrics["avg_ctr"]

            if avg_ctr < self.low_ctr_thr:
                calculated_conf += 0.2
                evidence.append(f"Average CTR {avg_ctr:.4f} is below threshold {self.low_ctr_thr}.")
            else:
                calculated_conf -= 0.2
                evidence.append(f"Average CTR {avg_ctr:.4f} is above threshold.")

        # --- Case 2: audience fatigue -----------------------------------------
        elif "audience fatigue" in text:
            # Check trend (CTR drop over time)
            df_sorted = df.sort_values("date")
            first_half = df_sorted.iloc[: len(df)//2]["ctr"].mean()
            second_half = df_sorted.iloc[len(df)//2 :]["ctr"].mean()

            if second_half < first_half:
                calculated_conf += 0.2
                evidence.append("CTR decreased from first half to second half → possible fatigue.")
            else:
                calculated_conf -= 0.1
                evidence.append("CTR did not decrease across time segments.")

        # --- Case 3: general hypothesis with ROAS ------------------------------
        elif "roas" in text:
            avg_roas = metrics["avg_roas"]
            if avg_roas < self.low_roas_thr:
                calculated_conf += 0.2
                evidence.append(f"Average ROAS {avg_roas:.2f} is below threshold {self.low_roas_thr}.")
            else:
                calculated_conf -= 0.1
                evidence.append(f"Average ROAS {avg_roas:.2f} is healthy.")

        # Fallback
        else:
            evidence.append("No matching evaluation rule. Defaulting to neutral adjustment.")

        # Keep within [0,1]
        calculated_conf = max(0.0, min(1.0, calculated_conf))

        return {
            "hypothesis": hypothesis["hypothesis"],
            "calculated_confidence": calculated_conf,
            "evidence": evidence
        }

    # -------------------------------------------------------------
    # 3️⃣ Validate entire hypothesis list + retry logic
    # -------------------------------------------------------------
    def run(self, hypotheses: list, df: pd.DataFrame):
        metrics = self.calculate_metrics(df)

        validated = []
        needs_retry = False

        for h in hypotheses:
            result = self.evaluate_hypothesis(h, metrics, df)
            validated.append(result)

            # Retry if any confidence < 0.6
            if result["calculated_confidence"] < 0.6:
                needs_retry = True

        return {
            "validated_hypotheses": validated,
            "metrics": metrics,
            "needs_retry": needs_retry
        }
