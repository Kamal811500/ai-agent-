"""Question generation engine."""

def set_rag_retriever(retriever):
    """Register RAG retriever."""
    pass

class QuestionEngine:
    """Generates interview questions."""
    def __init__(self, llm):
        self.llm = llm
