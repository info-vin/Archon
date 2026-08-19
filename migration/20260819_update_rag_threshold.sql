INSERT INTO archon_settings (key, value, description) 
VALUES ('LEAD_GEN_SIMILARITY_THRESHOLD', '0.70', 'RAG Cosine Similarity Threshold for Crawler Layer 1 Filtering')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
