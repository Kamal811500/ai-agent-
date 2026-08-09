"""
Technical Knowledge Base for RAG-powered interview questions and evaluation.
Covers all 12 days of the AI/ML Engineering curriculum.
"""
from __future__ import annotations
from typing import List, Dict, Any

KNOWLEDGE_BASE: List[Dict[str, Any]] = [

    # ── DAY 1: Python Fundamentals ────────────────────────────────────────────
    {
        "id": "py-001", "topic": "Python", "day": 1, "subtopic": "Data Structures",
        "title": "List vs Tuple vs Set vs Dict",
        "content": (
            "List: mutable ordered sequence. O(1) append/index, O(n) search/insert. "
            "Tuple: immutable ordered sequence. Hashable, lighter memory, used as dict keys. "
            "Set: unordered unique elements. O(1) average add/remove/lookup. Backed by hash table. "
            "Dict: hash map. O(1) average get/set/delete. Python 3.7+ preserves insertion order. "
            "Choosing correctly impacts both correctness and performance."
        ),
        "key_concepts": ["mutability", "hashability", "time complexity", "memory overhead", "insertion order"],
        "evaluation_criteria": "Candidate must explain mutability, O(1) vs O(n) operations, hashability, and give concrete use cases for each.",
        "excellent_indicators": ["mentions hashability", "discusses CPython memory layout", "gives real use cases", "performance trade-offs"],
        "poor_indicators": ["only says mutable vs immutable", "no mention of performance", "confuses set and dict"],
        "difficulty_context": {"easy": "mutability and basics", "medium": "performance and use cases", "hard": "CPython internals", "expert": "memory model, gc, weak refs"},
    },
    {
        "id": "py-002", "topic": "Python", "day": 1, "subtopic": "Functions",
        "title": "Decorators, Closures, and Higher-Order Functions",
        "content": (
            "Closure: a function that retains bindings from its enclosing scope even when called outside it. "
            "Decorator: syntactic sugar for wrapping a function with another function. Pattern: @decorator over def. "
            "Common uses: logging, auth, caching (functools.lru_cache), timing, retry logic. "
            "Decorator with arguments requires triple nesting: decorator_factory -> decorator -> wrapper. "
            "functools.wraps preserves __name__ and __doc__ of wrapped function."
        ),
        "key_concepts": ["closure", "scope", "LEGB rule", "functools.wraps", "decorator chaining", "parameterized decorators"],
        "evaluation_criteria": "Should explain closure mechanics, write a working decorator, handle arguments, discuss functools.wraps.",
        "excellent_indicators": ["implements decorator from scratch", "explains LEGB scope", "discusses functools.wraps importance", "class-based decorators"],
        "poor_indicators": ["only knows @staticmethod", "cannot write decorator from scratch", "confuses decorator and decorator factory"],
    },
    {
        "id": "py-003", "topic": "Python", "day": 1, "subtopic": "Generators",
        "title": "Generators, Iterators, and Memory Efficiency",
        "content": (
            "Generator: function with yield. Returns iterator. Lazy evaluation — values produced on demand. "
            "Memory efficient: O(1) vs O(n) for a list. "
            "Generator expression: (x for x in range(n)) vs list comprehension [x for x in range(n)]. "
            "send(), throw(), close() for coroutine-style communication. "
            "itertools: chain, islice, groupby, product — essential for efficient iteration. "
            "Use case: processing large files, infinite sequences, data pipelines."
        ),
        "key_concepts": ["yield", "lazy evaluation", "iterator protocol", "__iter__", "__next__", "StopIteration", "send()"],
        "evaluation_criteria": "Candidate should explain lazy evaluation, memory benefits, yield mechanics, and practical use cases.",
        "excellent_indicators": ["explains send() and coroutines", "discusses itertools", "compares memory usage", "infinite sequences"],
        "poor_indicators": ["cannot explain why generators save memory", "confuses generator and list comprehension", "does not know __iter__/__next__"],
    },
    {
        "id": "py-004", "topic": "Python", "day": 1, "subtopic": "Concurrency",
        "title": "GIL, Threads, Processes, and AsyncIO",
        "content": (
            "GIL (Global Interpreter Lock): mutex that allows only one thread to execute Python bytecode at a time. "
            "Threading: good for I/O-bound tasks (network, file). Due to GIL, not for CPU-bound. "
            "Multiprocessing: bypasses GIL by using separate processes. Good for CPU-bound tasks. "
            "AsyncIO: single-threaded event loop. async/await syntax. Best for high-concurrency I/O (HTTP clients, websockets). "
            "Comparison: threading < asyncio for I/O concurrency. multiprocessing for CPU parallelism. "
        ),
        "key_concepts": ["GIL", "race condition", "event loop", "coroutine", "async/await", "concurrent.futures", "asyncio.gather"],
        "evaluation_criteria": "Must explain GIL implications, when to use threads vs processes vs asyncio, and demonstrate async/await understanding.",
        "excellent_indicators": ["explains GIL mechanics", "discusses asyncio event loop internals", "concurrent.futures.ProcessPoolExecutor", "trio/anyio awareness"],
        "poor_indicators": ["thinks threading solves CPU parallelism", "confuses async and multi-thread", "does not know GIL"],
    },

    # ── DAY 2: OOP & Design Patterns ──────────────────────────────────────────
    {
        "id": "oop-001", "topic": "OOP", "day": 2, "subtopic": "SOLID Principles",
        "title": "SOLID Principles in Practice",
        "content": (
            "S - Single Responsibility: class has one reason to change. "
            "O - Open/Closed: open for extension, closed for modification. Use inheritance/composition. "
            "L - Liskov Substitution: subclass must be substitutable for base class without breaking behavior. "
            "I - Interface Segregation: many small interfaces better than one large. "
            "D - Dependency Inversion: depend on abstractions, not concretions. Use dependency injection. "
            "Violations: God classes (SRP), switch statements over types (OCP), overriding to raise NotImplementedError (LSP)."
        ),
        "key_concepts": ["cohesion", "coupling", "polymorphism", "dependency injection", "abstract base class"],
        "evaluation_criteria": "Candidate should name all 5, give concrete violation examples, and explain how each improves maintainability.",
        "excellent_indicators": ["gives real bug examples from experience", "discusses trade-offs", "mentions when NOT to apply"],
        "poor_indicators": ["cannot name all 5", "no concrete examples", "confuses SRP and ISP"],
    },
    {
        "id": "oop-002", "topic": "OOP", "day": 2, "subtopic": "Design Patterns",
        "title": "Gang of Four Patterns: Creational, Structural, Behavioral",
        "content": (
            "Creational: Singleton (one instance), Factory (delegate creation), Abstract Factory (families), Builder (complex objects), Prototype (clone). "
            "Structural: Adapter (interface conversion), Decorator (wrap to add behavior), Facade (simplified interface), Proxy (access control). "
            "Behavioral: Observer (pub-sub), Strategy (swap algorithms), Command (encapsulate requests), Iterator, Template Method. "
            "Anti-patterns: Singleton is often a global variable in disguise — hard to test. "
            "Python specifics: dataclasses, __slots__, metaclasses, __init_subclass__ for advanced patterns."
        ),
        "key_concepts": ["creational", "structural", "behavioral", "composition over inheritance", "dependency injection"],
        "evaluation_criteria": "Should identify patterns by category, explain intent and structure, give real-world examples, discuss trade-offs.",
        "excellent_indicators": ["discusses when NOT to use patterns", "shows Pythonic alternatives", "explains Observer as event system"],
        "poor_indicators": ["lists names without explanation", "confuses Decorator pattern with Python decorators", "no real examples"],
    },

    # ── DAY 3: Algorithms & Problem Solving ───────────────────────────────────
    {
        "id": "algo-001", "topic": "Algorithms", "day": 3, "subtopic": "Time Complexity",
        "title": "Big-O Analysis and Space-Time Trade-offs",
        "content": (
            "O(1): hash lookup, array index. O(log n): binary search, balanced BST. "
            "O(n): linear scan. O(n log n): merge sort, heapsort, efficient sorts. "
            "O(n²): bubble/selection sort, nested loops over same data. "
            "O(2^n): recursive fibonacci without memoization. O(n!): permutation generation. "
            "Amortized analysis: dynamic array append is O(1) amortized even though doubling is O(n). "
            "Space complexity: in-place O(1), recursion stack O(depth), memoization O(subproblems)."
        ),
        "key_concepts": ["asymptotic notation", "amortized", "best/worst/average case", "master theorem", "recurrence relation"],
        "evaluation_criteria": "Candidate should analyze code's time complexity correctly, discuss space trade-offs, and explain amortized analysis.",
        "excellent_indicators": ["derives complexity from code", "discusses cache effects", "explains amortized", "master theorem for recursion"],
        "poor_indicators": ["cannot analyze nested loop complexity", "confuses O(log n) and O(n log n)", "ignores space complexity"],
    },
    {
        "id": "algo-002", "topic": "Algorithms", "day": 3, "subtopic": "Dynamic Programming",
        "title": "Dynamic Programming: Memoization and Tabulation",
        "content": (
            "DP: break problem into overlapping subproblems, store results. "
            "Memoization (top-down): recursive + cache. Natural when recursion is cleaner. @functools.lru_cache. "
            "Tabulation (bottom-up): fill table iteratively. Often more memory efficient, no recursion stack. "
            "Identify DP: optimal substructure + overlapping subproblems. "
            "Classic problems: coin change, LCS, knapsack, edit distance, matrix chain multiplication, LIS. "
            "State design is key: what changes between subproblems defines the state."
        ),
        "key_concepts": ["optimal substructure", "overlapping subproblems", "state space", "transition function", "base case"],
        "evaluation_criteria": "Must identify DP applicability, define state clearly, write recurrence relation, implement correctly.",
        "excellent_indicators": ["identifies state space before coding", "discusses space optimization (1D vs 2D table)", "handles edge cases"],
        "poor_indicators": ["cannot define state", "applies brute force first without DP insight", "does not handle base cases"],
    },
    {
        "id": "algo-003", "topic": "Algorithms", "day": 3, "subtopic": "Graph Algorithms",
        "title": "BFS, DFS, Shortest Paths, and Graph Representations",
        "content": (
            "Representations: adjacency matrix O(V²) space, adjacency list O(V+E) space. "
            "BFS: level-order, shortest path in unweighted graph, O(V+E). "
            "DFS: connected components, topological sort, cycle detection, O(V+E). "
            "Dijkstra: shortest path weighted non-negative, O((V+E) log V) with min-heap. "
            "Bellman-Ford: handles negative weights, O(VE). "
            "A*: heuristic-guided Dijkstra, for pathfinding. "
            "Topological sort: Kahn's algorithm (BFS) or DFS post-order for DAGs."
        ),
        "key_concepts": ["cycle detection", "topological sort", "connected components", "shortest path", "spanning tree"],
        "evaluation_criteria": "Should choose correct algorithm for the problem, explain complexity, implement BFS/DFS from scratch.",
        "excellent_indicators": ["explains when Dijkstra fails (negative weights)", "discusses bidirectional BFS optimization", "Kahn's vs DFS for topological sort"],
        "poor_indicators": ["confuses BFS and DFS", "cannot implement graph traversal", "does not know when to use which algorithm"],
    },

    # ── DAY 4: Databases ──────────────────────────────────────────────────────
    {
        "id": "db-001", "topic": "Databases", "day": 4, "subtopic": "SQL Performance",
        "title": "Query Optimization, Indexes, and EXPLAIN",
        "content": (
            "Index types: B-tree (default, range queries), Hash (equality only), GIN (full-text, JSONB), BRIN (sequential data). "
            "Composite index: column order matters. Left-prefix rule. "
            "EXPLAIN ANALYZE: actual vs estimated rows, seq scan vs index scan. "
            "N+1 problem: load related records in one query. Use JOIN or eager loading. "
            "Slow query causes: missing index, full table scan, bad statistics, function on indexed column. "
            "Covering index: includes all columns in query, avoids heap fetch. "
            "Partitioning: range/list/hash. Reduces scan scope dramatically."
        ),
        "key_concepts": ["index types", "query plan", "seq scan", "N+1 problem", "covering index", "statistics", "vacuum"],
        "evaluation_criteria": "Must explain EXPLAIN output, identify why a query is slow, suggest indexes with justification, discuss N+1.",
        "excellent_indicators": ["reads EXPLAIN ANALYZE", "discusses index cardinality", "covering indexes", "partitioning strategy"],
        "poor_indicators": ["adds indexes without justification", "does not know N+1 problem", "cannot read query plan"],
    },
    {
        "id": "db-002", "topic": "Databases", "day": 4, "subtopic": "ACID and Transactions",
        "title": "ACID, Isolation Levels, and Distributed Transactions",
        "content": (
            "ACID: Atomicity (all-or-nothing), Consistency (constraints preserved), Isolation (concurrent transactions appear serial), Durability (committed = survived crash). "
            "Isolation levels: Read Uncommitted (dirty reads), Read Committed (most DBs default), Repeatable Read (MySQL default), Serializable (slowest, safest). "
            "Problems: dirty read, non-repeatable read, phantom read, lost update. "
            "MVCC (Multi-Version Concurrency Control): readers don't block writers. PostgreSQL/MySQL InnoDB. "
            "Distributed transactions: 2-phase commit (2PC), Saga pattern. "
            "Optimistic vs Pessimistic locking."
        ),
        "key_concepts": ["ACID", "isolation levels", "MVCC", "deadlock", "2PC", "saga", "optimistic locking"],
        "evaluation_criteria": "Should explain all ACID properties, isolation levels, when to use each, and handle concurrency problems.",
        "excellent_indicators": ["explains MVCC mechanism", "discusses Saga vs 2PC trade-offs", "identifies isolation level for given problem"],
        "poor_indicators": ["confuses consistency in ACID vs CAP", "does not know isolation levels", "cannot explain MVCC"],
    },

    # ── DAY 5: APIs & Backend ─────────────────────────────────────────────────
    {
        "id": "api-001", "topic": "APIs", "day": 5, "subtopic": "REST Design",
        "title": "REST API Design Principles and Best Practices",
        "content": (
            "REST constraints: stateless, client-server, cacheable, uniform interface, layered system. "
            "Resource naming: nouns not verbs. /users/{id}/orders not /getUserOrders. "
            "HTTP methods: GET (idempotent, safe), POST (create, not idempotent), PUT (full replace), PATCH (partial), DELETE. "
            "Status codes: 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauth, 403 Forbidden, 404 Not Found, 409 Conflict, 429 Rate Limited, 500 ISE. "
            "Versioning strategies: URL (/v1/), header, query param. "
            "Pagination: cursor-based (for large/real-time data), offset-based (simple). "
            "Rate limiting: token bucket, leaky bucket, fixed window, sliding window."
        ),
        "key_concepts": ["idempotency", "stateless", "HATEOAS", "versioning", "rate limiting", "pagination", "OpenAPI"],
        "evaluation_criteria": "Candidate should design a complete API, choose correct status codes, explain idempotency, discuss pagination strategies.",
        "excellent_indicators": ["explains idempotency implications", "discusses cursor vs offset pagination", "rate limiting algorithms", "OpenAPI/Swagger awareness"],
        "poor_indicators": ["uses POST for everything", "wrong status codes", "no versioning strategy", "cannot explain stateless"],
    },
    {
        "id": "api-002", "topic": "APIs", "day": 5, "subtopic": "Rate Limiting",
        "title": "Rate Limiting Algorithms and System Design",
        "content": (
            "Token bucket: tokens added at rate R, bucket capacity B. Allows burst up to B. "
            "Leaky bucket: processes at fixed rate regardless of burst. Queue-based. "
            "Fixed window: count per time window. Prone to double-rate at window boundary. "
            "Sliding window log: precise, memory O(requests). "
            "Sliding window counter: approximation with two fixed windows. Memory efficient. "
            "Implementation: Redis INCR + EXPIRE for distributed rate limiting. "
            "Lua scripts for atomicity. Return 429 Too Many Requests with Retry-After header."
        ),
        "key_concepts": ["token bucket", "leaky bucket", "sliding window", "Redis", "distributed rate limiting", "429 status"],
        "evaluation_criteria": "Should choose correct algorithm for requirements, explain trade-offs, describe distributed implementation.",
        "excellent_indicators": ["discusses boundary problem of fixed window", "Redis implementation details", "Retry-After header", "per-user vs global limiting"],
        "poor_indicators": ["knows only fixed window", "no distributed consideration", "does not discuss burst handling"],
    },

    # ── DAY 6: Machine Learning ───────────────────────────────────────────────
    {
        "id": "ml-001", "topic": "Machine Learning", "day": 6, "subtopic": "Bias-Variance",
        "title": "Bias-Variance Trade-off and Regularization",
        "content": (
            "Bias: error from wrong assumptions. High bias = underfitting. Simple model. "
            "Variance: sensitivity to training data. High variance = overfitting. Complex model. "
            "Trade-off: MSE = Bias² + Variance + Irreducible noise. "
            "Diagnosing: train vs val loss curves. High bias: both high. High variance: train low, val high. "
            "Regularization to reduce variance: L1 (Lasso, sparsity), L2 (Ridge, weight shrinkage), Dropout, Early stopping, Data augmentation, Batch normalization. "
            "Ensemble methods reduce variance: Bagging (Random Forest), Boosting (XGBoost)."
        ),
        "key_concepts": ["underfitting", "overfitting", "regularization", "L1", "L2", "dropout", "learning curves", "cross-validation"],
        "evaluation_criteria": "Must diagnose from learning curves, explain regularization mechanisms, discuss ensemble approaches.",
        "excellent_indicators": ["reads learning curves", "explains L1 sparsity vs L2 smoothness", "discusses dropout as ensemble", "validation strategies"],
        "poor_indicators": ["confuses bias and variance", "cannot diagnose from curves", "does not know regularization options"],
    },
    {
        "id": "ml-002", "topic": "Machine Learning", "day": 6, "subtopic": "Gradient Descent",
        "title": "Gradient Descent Variants and Optimization",
        "content": (
            "Batch GD: uses all data, stable but slow. "
            "SGD: one sample, noisy but fast updates, better generalization. "
            "Mini-batch: balance of both. Most common in practice. "
            "Momentum: accumulates past gradients. Escapes local minima. β~0.9. "
            "RMSprop: adaptive learning rate per parameter. "
            "Adam: momentum + RMSprop. Most popular optimizer. β1=0.9, β2=0.999, ε=1e-8. "
            "Learning rate scheduling: step decay, cosine annealing, warmup. "
            "Gradient clipping: prevents exploding gradients in RNNs."
        ),
        "key_concepts": ["learning rate", "momentum", "Adam", "saddle point", "local minima", "gradient clipping", "weight decay"],
        "evaluation_criteria": "Should explain Adam mechanics, learning rate impact, gradient problems, and when to use each variant.",
        "excellent_indicators": ["explains Adam's bias correction", "discusses learning rate finding", "gradient clipping for RNNs", "AdamW vs Adam"],
        "poor_indicators": ["only knows basic SGD", "does not know Adam formulas", "cannot explain momentum"],
    },
    {
        "id": "ml-003", "topic": "Machine Learning", "day": 6, "subtopic": "Evaluation",
        "title": "Model Evaluation Metrics and Cross-Validation",
        "content": (
            "Classification: Accuracy (misleading with imbalance), Precision (TP/(TP+FP)), Recall (TP/(TP+FN)), F1 (harmonic mean), ROC-AUC, PR-AUC. "
            "When to use each: high FP cost → high precision. High FN cost (cancer detection) → high recall. Imbalanced → PR-AUC over ROC-AUC. "
            "Regression: MSE, RMSE (same units as target), MAE (robust to outliers), R², MAPE. "
            "Cross-validation: k-fold, stratified k-fold (imbalanced), time-series CV (no data leakage), leave-one-out. "
            "Calibration: reliability diagram, Brier score, Platt scaling, isotonic regression."
        ),
        "key_concepts": ["precision", "recall", "F1", "ROC-AUC", "PR-AUC", "cross-validation", "calibration", "data leakage"],
        "evaluation_criteria": "Must choose correct metric for problem, explain trade-offs, design valid cross-validation strategy.",
        "excellent_indicators": ["explains PR-AUC vs ROC-AUC for imbalanced", "discusses calibration", "time-series CV leakage prevention"],
        "poor_indicators": ["uses accuracy for imbalanced data", "confuses precision and recall", "no awareness of data leakage in CV"],
    },

    # ── DAY 7: Deep Learning ──────────────────────────────────────────────────
    {
        "id": "dl-001", "topic": "Deep Learning", "day": 7, "subtopic": "Backpropagation",
        "title": "Backpropagation, Vanishing/Exploding Gradients",
        "content": (
            "Backprop: chain rule applied layer by layer. Compute gradient of loss w.r.t. each weight. "
            "Vanishing gradient: gradients become exponentially small in deep networks. "
            "Caused by: sigmoid/tanh activation derivatives < 1, multiplied across many layers. "
            "Solutions: ReLU activations, batch normalization, residual connections (ResNet), LSTM gates. "
            "Exploding gradient: gradients grow exponentially. Solution: gradient clipping. "
            "Xavier/He initialization: correct variance for activations to avoid vanishing/exploding at init. "
            "Batch normalization: normalizes layer inputs, stabilizes training, allows higher learning rates."
        ),
        "key_concepts": ["chain rule", "vanishing gradient", "ReLU", "batch norm", "residual connections", "He initialization", "gradient flow"],
        "evaluation_criteria": "Must explain chain rule, identify causes of vanishing gradients, list solutions and mechanisms.",
        "excellent_indicators": ["derives backprop equations", "explains residual connections as gradient highway", "discusses initialization schemes"],
        "poor_indicators": ["cannot explain chain rule", "does not know why sigmoid causes vanishing", "no awareness of solutions"],
    },
    {
        "id": "dl-002", "topic": "Deep Learning", "day": 7, "subtopic": "Architectures",
        "title": "CNN, RNN, LSTM architectures and use cases",
        "content": (
            "CNN: local receptive fields, weight sharing. Convolutional layer → Pooling → FC. "
            "Good for: images (translation invariance), 1D sequences with local patterns (text, audio). "
            "RNN: sequential processing, hidden state carries context. Vanishing gradient over long sequences. "
            "LSTM: input gate, forget gate, output gate, cell state. Solves long-term dependency. "
            "GRU: simpler than LSTM, fewer parameters, similar performance. Reset and update gates. "
            "Modern: Transformers outperform RNNs for most NLP tasks due to parallelism and global attention."
        ),
        "key_concepts": ["convolution", "pooling", "recurrent", "LSTM gates", "GRU", "attention", "long-range dependency"],
        "evaluation_criteria": "Should choose correct architecture for task, explain mechanism, discuss limitations and modern alternatives.",
        "excellent_indicators": ["explains LSTM gate mechanics", "discusses why Transformers replaced RNNs", "talks about receptive field"],
        "poor_indicators": ["cannot explain LSTM gates", "does not know CNN's inductive biases", "no awareness of Transformers"],
    },

    # ── DAY 8: LLMs & Transformers ────────────────────────────────────────────
    {
        "id": "llm-001", "topic": "LLMs", "day": 8, "subtopic": "Attention",
        "title": "Self-Attention, Multi-Head Attention, and Complexity",
        "content": (
            "Self-attention: each token attends to all others. Q, K, V = linear projections of input. "
            "Attention(Q,K,V) = softmax(QKᵀ/√d_k)V. Scale by √d_k prevents softmax saturation. "
            "O(n²) in sequence length — quadratic memory. Problem for long sequences. "
            "Multi-head: run h attention heads in parallel, concatenate outputs. Captures different relationship types. "
            "Positional encoding: sin/cos or learned. Gives position information (self-attention is permutation-invariant). "
            "Flash Attention: IO-aware exact attention in O(n) memory using tiling. "
            "Alternatives for long context: Linformer, Longformer, sliding window attention, ALiBi."
        ),
        "key_concepts": ["Q K V", "softmax scaling", "multi-head", "positional encoding", "Flash Attention", "O(n²) complexity"],
        "evaluation_criteria": "Must derive attention formula, explain multi-head motivation, discuss O(n²) limitation and solutions.",
        "excellent_indicators": ["derives attention from first principles", "explains why scaling by √d_k", "discusses Flash Attention", "KV cache for inference"],
        "poor_indicators": ["cannot write attention formula", "does not know why multi-head", "no awareness of complexity problem"],
    },
    {
        "id": "llm-002", "topic": "LLMs", "day": 8, "subtopic": "Fine-tuning",
        "title": "Fine-tuning, RLHF, LoRA, and Prompt Engineering",
        "content": (
            "Full fine-tuning: update all weights. Expensive, catastrophic forgetting risk. "
            "PEFT (Parameter-Efficient Fine-Tuning): update small subset of parameters. "
            "LoRA: add low-rank matrices A·B to weight matrices. Rank r << d. Only train A,B. "
            "QLoRA: quantize base model to 4-bit, add LoRA adapters. Fits 70B model on 48GB GPU. "
            "RLHF: pre-train → SFT → reward model → PPO. Aligns model to human preferences. "
            "DPO: simpler alternative to RLHF. Direct preference optimization. No reward model needed. "
            "Prompt engineering: zero-shot, few-shot, CoT (chain-of-thought), ReAct, tree-of-thought."
        ),
        "key_concepts": ["LoRA", "QLoRA", "RLHF", "DPO", "SFT", "catastrophic forgetting", "PEFT", "chain-of-thought"],
        "evaluation_criteria": "Should explain LoRA mechanism, compare RLHF vs DPO, discuss prompt engineering strategies.",
        "excellent_indicators": ["explains LoRA rank selection", "discusses catastrophic forgetting mitigation", "DPO vs PPO trade-offs"],
        "poor_indicators": ["does not know LoRA", "thinks fine-tuning always requires full weights", "no awareness of alignment techniques"],
    },
    {
        "id": "llm-003", "topic": "LLMs", "day": 8, "subtopic": "RAG",
        "title": "Retrieval-Augmented Generation (RAG) Architecture",
        "content": (
            "RAG: combines retrieval with generation to ground LLM responses in external knowledge. "
            "Components: document loader → chunker → embedder → vector store → retriever → LLM. "
            "Chunking: fixed-size, sentence, paragraph. Overlap prevents context loss at boundaries. "
            "Embeddings: dense (semantic similarity), sparse (BM25, keyword). Hybrid retrieval combines both. "
            "Vector stores: FAISS, Pinecone, Weaviate, Chroma. "
            "Advanced: HyDE (hypothetical document embeddings), reranking (cross-encoder), query expansion. "
            "Evaluation: retrieval recall, context relevance, answer faithfulness, answer relevance."
        ),
        "key_concepts": ["chunking", "embedding", "vector store", "retrieval", "reranking", "hybrid search", "faithfulness"],
        "evaluation_criteria": "Must describe complete RAG pipeline, discuss chunking strategies, embedding choices, and evaluation metrics.",
        "excellent_indicators": ["discusses hybrid retrieval", "reranking with cross-encoder", "RAG failure modes", "evaluation framework"],
        "poor_indicators": ["only knows simple embedding search", "no awareness of chunking strategies", "cannot discuss failure modes"],
    },

    # ── DAY 9: MLOps ──────────────────────────────────────────────────────────
    {
        "id": "mlops-001", "topic": "MLOps", "day": 9, "subtopic": "Data Drift",
        "title": "Data Drift, Model Drift Detection and Monitoring",
        "content": (
            "Covariate shift: input distribution changes. Concept drift: relationship P(y|x) changes. "
            "Label shift: target distribution changes. "
            "Detection methods: PSI (Population Stability Index), KL divergence, Kolmogorov-Smirnov test, chi-squared. "
            "Monitoring metrics: input feature statistics, prediction distribution, business KPIs. "
            "Model degradation signals: accuracy drop, confidence distribution shift. "
            "Response: retrain trigger (scheduled, performance-based, drift-based). "
            "Tools: Evidently AI, Arize, Whylogs, Seldon Alibi Detect. "
            "Shadow mode: run new model alongside production, compare predictions."
        ),
        "key_concepts": ["covariate shift", "concept drift", "PSI", "KL divergence", "KS test", "retraining strategy", "shadow mode"],
        "evaluation_criteria": "Must define types of drift, explain detection methods statistically, design monitoring pipeline.",
        "excellent_indicators": ["distinguishes covariate vs concept drift", "explains PSI thresholds", "discusses shadow deployment"],
        "poor_indicators": ["only knows accuracy degradation", "no statistical detection methods", "cannot design monitoring pipeline"],
    },
    {
        "id": "mlops-002", "topic": "MLOps", "day": 9, "subtopic": "Deployment",
        "title": "Model Serving, CI/CD for ML, and Feature Stores",
        "content": (
            "Serving patterns: REST API (Flask/FastAPI), gRPC (lower latency), batch inference, streaming. "
            "Canary deployment: gradual traffic shift. Blue-green: switch instantly, easy rollback. "
            "Feature store: central repository for features. Offline (training) + Online (serving) stores. "
            "Offline: S3/Delta Lake/BigQuery. Online: Redis/DynamoDB for low-latency lookups. "
            "MLflow: experiment tracking, model registry, model serving. "
            "Kubeflow: ML pipelines on Kubernetes. "
            "A/B testing for models: statistical significance, minimum detectable effect, power analysis. "
            "Model registry: versioning, staging, production promotion."
        ),
        "key_concepts": ["canary deployment", "feature store", "model registry", "A/B testing", "MLflow", "online vs offline"],
        "evaluation_criteria": "Should design deployment pipeline, explain feature store motivation, discuss A/B testing setup.",
        "excellent_indicators": ["explains online/offline feature store duality", "designs statistically valid A/B test", "discusses shadow mode"],
        "poor_indicators": ["does not know feature store concept", "no deployment strategy beyond basic deploy", "cannot design A/B test"],
    },

    # ── DAY 10: System Design ─────────────────────────────────────────────────
    {
        "id": "sd-001", "topic": "System Design", "day": 10, "subtopic": "Distributed Systems",
        "title": "CAP Theorem, Consistency Models, and Distributed Patterns",
        "content": (
            "CAP: Consistency, Availability, Partition Tolerance. Can only guarantee 2 of 3 during partition. "
            "CP: ZooKeeper, HBase. AP: Cassandra, DynamoDB (eventual consistency). "
            "PACELC: extends CAP to include latency vs consistency even without partitions. "
            "Consistency models: strong, linearizable, sequential, causal, eventual. "
            "Patterns: leader election (Raft, Paxos), distributed locking (Redlock), distributed tracing (Jaeger/Zipkin). "
            "Saga pattern: distributed transactions via events. Choreography vs Orchestration. "
            "Circuit breaker: prevent cascade failure. States: Closed, Open, Half-Open."
        ),
        "key_concepts": ["CAP", "consistency models", "Raft", "eventual consistency", "saga", "circuit breaker", "PACELC"],
        "evaluation_criteria": "Must explain CAP with examples, choose consistency model for requirement, design distributed transaction.",
        "excellent_indicators": ["explains PACELC as extension", "discusses Raft vs Paxos", "Saga choreography vs orchestration"],
        "poor_indicators": ["confuses CAP consistency with ACID consistency", "cannot give CP/AP examples", "does not know circuit breaker"],
    },
    {
        "id": "sd-002", "topic": "System Design", "day": 10, "subtopic": "Scalability",
        "title": "Horizontal Scaling, Caching, Message Queues, CDN",
        "content": (
            "Vertical: bigger machine. Horizontal: more machines. Stateless services scale horizontally. "
            "Load balancing: round-robin, least connections, consistent hashing (for sticky sessions/caches). "
            "Caching layers: L1 (in-process), L2 (Redis/Memcached), L3 (CDN). "
            "Cache strategies: Cache-aside, Read-through, Write-through, Write-back. "
            "Cache invalidation: the hardest problem. TTL, event-driven, cache-through. "
            "Message queues: Kafka (high-throughput, log-based), RabbitMQ (traditional, AMQP). "
            "CDN: edge caching, reduces origin load. Cache-Control headers control TTL. "
            "Database sharding: horizontal, by key range or hash. Cross-shard queries expensive."
        ),
        "key_concepts": ["consistent hashing", "cache invalidation", "Kafka", "sharding", "CDN", "load balancing", "stateless"],
        "evaluation_criteria": "Design scalable system with correct caching strategy, sharding approach, and message queue choice.",
        "excellent_indicators": ["explains consistent hashing for caches", "discusses cache invalidation strategies", "Kafka partition strategy"],
        "poor_indicators": ["no caching strategy", "ignores cache invalidation", "cannot explain message queue benefits"],
    },

    # ── DAY 11: Cloud & Infrastructure ────────────────────────────────────────
    {
        "id": "cloud-001", "topic": "Cloud", "day": 11, "subtopic": "Kubernetes",
        "title": "Kubernetes vs Serverless, Container Orchestration",
        "content": (
            "Kubernetes: container orchestration. Pods, Deployments, Services, ConfigMaps, Secrets. "
            "HPA (Horizontal Pod Autoscaler): scale based on CPU/memory/custom metrics. "
            "Serverless (Lambda/Cloud Functions): no server management, event-driven, pay-per-invocation. "
            "K8s advantages: persistent workloads, fine-grained control, multi-container pods, stateful sets. "
            "Serverless advantages: zero idle cost, automatic scaling, simpler ops. "
            "Cold start problem in serverless: mitigation via provisioned concurrency. "
            "Service mesh (Istio): mTLS, traffic management, observability without code changes. "
            "Helm: Kubernetes package manager. GitOps: ArgoCD, Flux."
        ),
        "key_concepts": ["pods", "deployments", "HPA", "serverless cold start", "service mesh", "GitOps", "Helm"],
        "evaluation_criteria": "Should compare K8s vs serverless, explain pod lifecycle, design autoscaling strategy.",
        "excellent_indicators": ["explains cold start mitigation", "discusses service mesh value", "GitOps workflow", "stateful sets for databases"],
        "poor_indicators": ["cannot explain difference between Deployment and StatefulSet", "no awareness of cold starts", "no scaling strategy"],
    },

    # ── DAY 12: Security & Ethics ─────────────────────────────────────────────
    {
        "id": "sec-001", "topic": "Security", "day": 12, "subtopic": "LLM Security",
        "title": "Prompt Injection, Jailbreaks, and LLM Security",
        "content": (
            "Prompt injection: attacker embeds instructions in user input to override system prompt. "
            "Direct injection: user crafts prompt that ignores system instructions. "
            "Indirect injection: malicious content in retrieved documents (RAG) injects instructions. "
            "Defenses: input/output validation, delimiters, prompt hardening, privilege separation. "
            "Jailbreaks: roleplay, DAN, base64 encoding, token smuggling, many-shot. "
            "LLM firewall: classify inputs before sending to LLM. "
            "Output validation: check for PII leakage, harmful content, instruction leakage. "
            "Principle of least privilege in agent systems: agents should not have more capability than needed."
        ),
        "key_concepts": ["prompt injection", "indirect injection", "jailbreak", "privilege separation", "input validation", "output validation"],
        "evaluation_criteria": "Must explain direct vs indirect injection, list defenses with mechanisms, design secure LLM pipeline.",
        "excellent_indicators": ["explains indirect injection via RAG", "discusses architectural defenses", "least privilege for agents"],
        "poor_indicators": ["only knows jailbreaks", "no awareness of indirect injection", "no defensive architecture"],
    },
    {
        "id": "sec-002", "topic": "Security", "day": 12, "subtopic": "AI Ethics",
        "title": "AI Bias, Fairness, Explainability, and Responsible AI",
        "content": (
            "Bias sources: historical data bias, label bias, sampling bias, measurement bias. "
            "Fairness metrics: demographic parity, equalized odds, individual fairness. These are often in conflict. "
            "Impossibility theorem: cannot satisfy all fairness metrics simultaneously. "
            "Explainability: SHAP (Shapley values), LIME (local approximation), attention visualization. "
            "Interpretable models: decision trees, linear regression, rule-based. "
            "Model cards: structured documentation of model capabilities, limitations, bias evaluations. "
            "Differential privacy: add calibrated noise to protect individual records in training. ε-differential privacy. "
            "Federated learning: train on device, aggregate updates — privacy without centralizing data."
        ),
        "key_concepts": ["bias", "fairness", "SHAP", "LIME", "model cards", "differential privacy", "federated learning"],
        "evaluation_criteria": "Should explain fairness metrics and their conflicts, explain SHAP, discuss responsible AI practices.",
        "excellent_indicators": ["explains impossibility theorem", "discusses SHAP derivation", "differential privacy ε interpretation"],
        "poor_indicators": ["defines bias without specifics", "does not know SHAP", "no awareness of fairness trade-offs"],
    },
]
