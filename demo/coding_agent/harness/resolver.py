"""
Context Resolver - Garry Tan's Resolver Concept
==============================================

The Resolver is a routing table for context:
- "When task type X appears, load document Y first"
- This is Mario Zechner's "transparency" principle in action

The resolver answers: "What context should I load, and when?"
"""


class Context:
    """Represents loaded context (documents + metadata)."""

    def __init__(self, task_type: str, documents: list[dict]):
        self.task_type = task_type
        self.documents = documents
        self.loaded_files = [doc["path"] for doc in documents]

    def __repr__(self):
        return f"Context(type={self.task_type}, files={self.loaded_files})"

    @classmethod
    def empty(cls):
        return cls(task_type="unknown", documents=[])


class Resolver:
    """
    Context routing table - Garry Tan's Resolver concept.

    Maps task types to the documents that should be loaded.
    No hidden injections - everything is explicit.

    Example:
        resolver = Resolver()
        ctx = resolver.route("investigate a bug in auth")
        # ctx.task_type = "investigate"
        # ctx.documents = [{"path": "skills/investigate.md", "content": ...}]
    """

    def __init__(self):
        # Routing table: task_type → list of document paths
        # This replaces the "20000 line CLAUDE.md" anti-pattern
        self.routing_table = {
            "investigate": [
                "skills/investigate.md",
                "docs/investigation_guide.md",
            ],
            "enrich": [
                "skills/enrich.md",
                "docs/data_sources.md",
            ],
            "match": [
                "skills/match.md",
                "docs/matching_rules.md",
            ],
            "bug": [
                "docs/debugging.md",
                "context/recent_commits.md",
            ],
            "architecture": [
                "docs/architecture.md",
                "context/team_decisions.md",
            ],
            "refactor": [
                "docs/coding_standards.md",
                "context/code_review_history.md",
            ],
        }

        # Default documents to always load
        self.default_docs = [
            "docs/system_prompt.md",
        ]

    def classify(self, task: str) -> str:
        """
        Classify the task type based on keywords.

        In production, this would use an LLM for better classification.
        For demo purposes, we use simple keyword matching.
        """
        task_lower = task.lower()

        # Check routing table keywords
        for task_type, docs in self.routing_table.items():
            if task_type in task_lower:
                return task_type

        # Fallback keyword checks
        if any(kw in task_lower for kw in ["bug", "error", "fix", "crash"]):
            return "bug"
        elif any(kw in task_lower for kw in ["architect", "design", "structure"]):
            return "architecture"
        elif any(kw in task_lower for kw in ["refactor", "restructure", "reorganize"]):
            return "refactor"

        return "general"

    def route(self, task: str) -> Context:
        """
        Route a task to the appropriate context.

        Returns a Context object with the task type and documents to load.

        This is the KEY to Garry Tan's architecture:
        - Skills say HOW
        - Resolver says WHAT to load WHEN
        """
        task_type = self.classify(task)
        docs_to_load = self.routing_table.get(task_type, [])

        documents = []
        for doc_path in docs_to_load:
            # In production, would actually read the file
            documents.append({
                "path": doc_path,
                "content": f"[Content of {doc_path}]",
            })

        # Add default docs
        for doc_path in self.default_docs:
            documents.append({
                "path": doc_path,
                "content": f"[Content of {doc_path}]",
            })

        ctx = Context(task_type=task_type, documents=documents)

        print(f"  Resolver: classified as '{task_type}', loading {len(documents)} documents")
        for doc in documents:
            print(f"    - {doc['path']}")

        return ctx


class TransparentResolver(Resolver):
    """
    Extended resolver with full transparency logging.

    Mario Zechner's principle: "无后台注入，所有上下文修改可追溯"
    """

    def __init__(self):
        super().__init__()
        self.routing_log: list[dict] = []

    def route(self, task: str) -> Context:
        """Route with full logging for transparency."""
        task_type = self.classify(task)
        ctx = super().route(task)

        # Log for transparency
        self.routing_log.append({
            "task": task,
            "task_type": task_type,
            "loaded_files": ctx.loaded_files,
        })

        return ctx

    def get_routing_history(self) -> list[dict]:
        """Return the full routing history for debugging."""
        return self.routing_log
