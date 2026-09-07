from prometheus_client import Counter, Histogram, Gauge

# Custom Business Metrics for AI
TICKET_PROCESSED_COUNT = Counter(
    'ai_ticket_processed_total',
    'Total number of tickets processed by AI',
    ['category', 'priority']
)

AI_CONFIDENCE_SCORE = Histogram(
    'ai_confidence_score',
    'Confidence score of the AI prediction',
    buckets=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0)
)
