"""Answer evaluation engine."""

def set_rag_retriever(retriever):
    """Register RAG retriever."""
    pass

class AnswerEvaluator:
    """Evaluates candidate answers."""
    def __init__(self, llm):
        self.llm = llm
