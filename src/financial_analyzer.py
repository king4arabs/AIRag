import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """Analyze tabular financial data supplied as a pandas DataFrame."""

    def __init__(self, data: pd.DataFrame):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")
        self.data = data
        self._results: dict | None = None

    def analyze(self) -> dict:
        """Run a suite of financial analyses and cache the results."""
        numeric_df = self.data.select_dtypes(include=[np.number])
        if numeric_df.empty:
            self._results = {"summary": "No numeric columns found for analysis."}
            return self._results

        results: dict = {}
        results["descriptive_stats"] = numeric_df.describe().to_dict()
        results["column_totals"] = numeric_df.sum().to_dict()
        results["column_means"] = numeric_df.mean().to_dict()
        results["column_medians"] = numeric_df.median().to_dict()

        # Growth rates (row-over-row percentage change)
        if len(numeric_df) > 1:
            pct = numeric_df.pct_change().dropna()
            results["avg_growth_rate"] = pct.mean().to_dict()

        # Correlation matrix
        if numeric_df.shape[1] > 1:
            results["correlation"] = numeric_df.corr().to_dict()

        self._results = results
        logger.info("Financial analysis completed for %d rows × %d numeric columns",
                     len(numeric_df), numeric_df.shape[1])
        return results

    def get_results(self) -> dict:
        """Return cached analysis results, running analyze() if needed."""
        if self._results is None:
            self.analyze()
        return self._results

    def get_summary_text(self) -> str:
        """Return a human-readable summary of the analysis."""
        results = self.get_results()
        if "summary" in results:
            return results["summary"]

        lines = ["Financial Analysis Summary", "=" * 40]
        if "column_totals" in results:
            lines.append("\nColumn Totals:")
            for col, val in results["column_totals"].items():
                lines.append(f"  {col}: {val:,.2f}")
        if "column_means" in results:
            lines.append("\nColumn Averages:")
            for col, val in results["column_means"].items():
                lines.append(f"  {col}: {val:,.2f}")
        if "avg_growth_rate" in results:
            lines.append("\nAverage Growth Rates:")
            for col, val in results["avg_growth_rate"].items():
                lines.append(f"  {col}: {val:.2%}")
        return "\n".join(lines)