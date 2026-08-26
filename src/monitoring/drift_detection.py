import pandas as pd
from scipy.stats import ks_2samp
import logging

logger = logging.getLogger(__name__)

def detect_drift(reference_data: pd.Series, current_data: pd.Series, threshold: float = 0.05):
    """
    Perform Kolmogorov-Smirnov test to detect data drift between two distributions.
    E.g. text lengths or predicted confidences.
    """
    stat, p_value = ks_2samp(reference_data, current_data)
    
    if p_value < threshold:
        logger.warning(f"Data Drift Detected! KS Statistic: {stat:.4f}, p-value: {p_value:.4f}")
        return True
    
    logger.info(f"No significant drift. KS Statistic: {stat:.4f}, p-value: {p_value:.4f}")
    return False
