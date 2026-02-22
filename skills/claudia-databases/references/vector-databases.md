# Vector Databases

## What They're For

Vector databases store and query high-dimensional embeddings -- numerical representations of text, images, or other data. The core operation is "find me the N most similar vectors to this one" (nearest neighbor search).

**Primary use cases:**
- RAG (Retrieval Augmented Generation) -- find relevant documents for LLM context
- Semantic search -- search by meaning, not keywords
- Recommendation systems -- find similar items/users
- Image search -- find visually similar images
- Anomaly detection -- find outliers in embedding space

## Options Comparison

| Database | Type | Best For | Hosting |
|----------|------|----------|---------|
| pgvector | Postgres extension | <5M vectors, already using Postgres | Self-hosted or managed Postgres |
| Pinecone | Managed service | Production RAG, low-ops teams | SaaS only |
| Qdrant | Purpose-built | High performance, filtering + vectors | Self-hosted or cloud |
| Weaviate | Purpose-built | Multi-modal (text + images), GraphQL API | Self-hosted or cloud |
| Chroma | Embedded | Prototyping, local dev, small datasets | Embedded (Python) |
| Milvus | Purpose-built | Large scale (billions of vectors) | Self-hosted or Zilliz Cloud |

## Decision Framework

```
How many vectors?
├── <100K → SQLite + sqlite-vss or Chroma (just prototype)
├── <1M → pgvector (if already using Postgres)
├── 1M-10M → pgvector with HNSW index, or Qdrant
├── 10M-100M → Qdrant, Weaviate, or Pinecone
└── >100M → Milvus or Pinecone (enterprise tier)
```

```
Do you need filtering + vector search?
├── Simple metadata filters → pgvector WHERE clauses
├── Complex filters + vectors → Qdrant (best at hybrid filtering)
└── Full-text + vectors → Weaviate or Elasticsearch with kNN
```

## pgvector: The Pragmatic Default

If you're already using PostgreSQL, start with pgvector:

```sql
-- Enable the extension
CREATE EXTENSION vector;

-- Create a table with an embedding column
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  content TEXT,
  embedding vector(1536)  -- dimension matches your model (OpenAI = 1536)
);

-- Create an HNSW index for fast similarity search
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- Query: find 5 most similar documents
SELECT content, embedding <=> '[0.1, 0.2, ...]'::vector AS distance
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

**Pros:** No new infrastructure, full SQL power, transactions, joins with your other data.
**Cons:** Slower than purpose-built at scale, HNSW index build can be slow for large datasets.

## Embedding Models

Your choice of embedding model matters as much as your vector DB:

| Model | Dimensions | Best For | Notes |
|-------|-----------|----------|-------|
| OpenAI text-embedding-3-small | 1536 | General text | Good quality, API dependency |
| OpenAI text-embedding-3-large | 3072 | Higher quality text | Better but 2x storage |
| Cohere embed-v3 | 1024 | Multilingual | Good multilingual support |
| BGE / GTE (open source) | 768-1024 | Local/private | No API dependency, run locally |
| CLIP | 512-768 | Images + text | Multi-modal search |

**Recommendation for most cases:** Start with OpenAI's small model. Switch to open-source (BGE) if you need local/private processing or want to avoid API costs at scale.

## Key Concepts

- **HNSW**: Hierarchical Navigable Small World -- the standard index type. Faster queries, more memory, slower builds.
- **IVF**: Inverted File Index -- less memory, slower queries, faster builds. Good for very large datasets.
- **Distance metrics**: Cosine (most common for text), L2/Euclidean (spatial data), Inner Product (when vectors are normalized).
- **Dimensionality**: Higher = more expressive but more storage/compute. 1536 is the sweet spot for most text.
