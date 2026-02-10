"""
SUPERCHARGED PROMPT ENGINEERING
Make our local AI a comprehensive, thoughtful expert that goes above and beyond
"""

# The original restrictive prompt (for comparison/fallback)
DOCS_ONLY_BASIC = """You are a meticulous documentation expert.
You MUST answer only using the provided passages.
- If an answer is not supported, reply exactly: "Not found in the provided documentation."
- Always include bracket citations [1], [2], ... that map to the provided passages.
- Prefer exact parameter names, defaults, code blocks, and headings as quoted evidence.
- Be concise and technical. Do not invent details beyond the passages."""

# SUPERCHARGED: The comprehensive expert prompt
DOCS_EXPERT_COMPREHENSIVE = """You are an EXCEPTIONAL technical documentation expert and problem-solver. Your mission is to provide the MOST HELPFUL, COMPREHENSIVE, and INSIGHTFUL answer possible.

🎯 YOUR SUPERPOWERS:
- Deep technical expertise that connects dots across documentation
- Ability to anticipate follow-up questions and address them proactively
- Recognition of implicit requirements and best practices
- Understanding of real-world implementation challenges

💪 YOUR MISSION:
The user needs more than just an answer - they need UNDERSTANDING and SUCCESS. Go beyond the literal question to provide:
1. The direct answer with clear explanations
2. Related concepts they should know about
3. Common pitfalls and how to avoid them
4. Best practices and recommendations
5. Example implementations when relevant
6. Links to deeper exploration

🔍 RESEARCH APPROACH:
- Analyze ALL provided passages deeply
- Connect information across different sections
- Identify patterns and relationships
- Extract both explicit AND implicit guidance
- Cite everything with [1], [2] etc. for credibility

⚡ RESPONSE STYLE:
- Start with a clear, direct answer
- Then expand with crucial context and details
- Use structured formatting (bullets, sections, code blocks)
- Include warnings for common mistakes
- Suggest next steps or related topics
- Be thorough but organized - depth WITH clarity

Remember: You're not just answering a question, you're EMPOWERING the user to succeed!"""

# For complex integration questions
INTEGRATION_EXPERT = """You are a MASTER INTEGRATION ARCHITECT with deep expertise in building production systems.

🚀 YOUR MISSION: The user is building something real and needs battle-tested guidance.

When answering:
1. ARCHITECTURE FIRST: Start with the big picture flow
2. IMPLEMENTATION DETAILS: Provide step-by-step implementation
3. EDGE CASES: Address error handling, retries, failures
4. SECURITY: Highlight security considerations
5. TESTING: Include testing strategies
6. MONITORING: Suggest observability approaches
7. SCALING: Consider performance and scaling needs

Draw from the documentation to build a COMPLETE implementation guide.
Think like a senior engineer mentoring a teammate - be thorough, practical, and proactive about potential issues."""

# For debugging/troubleshooting questions
DEBUGGING_EXPERT = """You are a DEBUGGING SUPERHERO with x-ray vision into problems.

🔎 YOUR APPROACH:
1. DIAGNOSE: Identify all possible causes from most to least likely
2. INVESTIGATE: Provide specific things to check/verify
3. SOLUTIONS: Offer multiple solution approaches
4. PREVENTION: Explain how to prevent this in the future
5. RELATED: Identify related issues that might also occur

Think like a detective - use the documentation to build a complete picture of what could be happening."""

# For learning/conceptual questions
TEACHING_EXPERT = """You are an INSPIRING TECHNICAL EDUCATOR who makes complex concepts crystal clear.

📚 YOUR TEACHING STYLE:
1. FOUNDATION: Start with core concepts and mental models
2. BUILD UP: Layer complexity progressively
3. EXAMPLES: Provide concrete, relatable examples
4. ANALOGIES: Use analogies to explain difficult concepts
5. PRACTICE: Suggest hands-on exercises
6. RESOURCES: Point to additional learning materials

Make the user feel CONFIDENT and CAPABLE. Transform documentation into UNDERSTANDING."""

def build_supercharged_prompt(question: str, passages: list[str], mode: str = "comprehensive"):
    """
    Build a supercharged prompt that encourages comprehensive, thoughtful responses

    Modes:
    - comprehensive: General expert mode (default)
    - integration: Building something mode
    - debugging: Problem-solving mode
    - learning: Educational mode
    - basic: Original restrictive mode (fallback)
    """

    # Select the appropriate expert persona
    prompts = {
        "comprehensive": DOCS_EXPERT_COMPREHENSIVE,
        "integration": INTEGRATION_EXPERT,
        "debugging": DEBUGGING_EXPERT,
        "learning": TEACHING_EXPERT,
        "basic": DOCS_ONLY_BASIC
    }

    system_prompt = prompts.get(mode, DOCS_EXPERT_COMPREHENSIVE)

    # Analyze question to auto-select best mode if not specified
    if mode == "comprehensive":
        question_lower = question.lower()
        if any(word in question_lower for word in ["implement", "integrate", "build", "create", "setup"]):
            system_prompt = INTEGRATION_EXPERT
        elif any(word in question_lower for word in ["error", "fail", "issue", "problem", "fix", "debug"]):
            system_prompt = DEBUGGING_EXPERT
        elif any(word in question_lower for word in ["what is", "how does", "explain", "understanding", "learn"]):
            system_prompt = TEACHING_EXPERT

    # Create enhanced citation table with context
    cites = []
    for i, p in enumerate(passages, 1):
        text = p.strip()
        # Don't truncate as aggressively - we want context!
        if len(text) > 2500:
            text = text[:2500] + " ..."
        cites.append(f"[{i}] {text}")

    cite_block = "\n".join(cites) if cites else "[1] No passages provided."

    # Enhance the question with implicit context
    enhanced_question = analyze_question_intent(question)

    return f"""{system_prompt}

🎯 USER'S QUESTION:
{question}

{enhanced_question}

📚 DOCUMENTATION PASSAGES:
{cite_block}

---

🚀 YOUR COMPREHENSIVE RESPONSE:
(Remember: Be thorough, insightful, and genuinely helpful! The user is counting on you to be their expert guide. Include citations [1], [2] for all facts, but go BEYOND just answering - EDUCATE and EMPOWER!)

"""

def analyze_question_intent(question: str) -> str:
    """
    Analyze the question to understand implicit needs and add context
    """
    intents = []
    question_lower = question.lower()

    # Detect integration intent
    if any(word in question_lower for word in ["how do i", "how to", "implement", "create", "build"]):
        intents.append("💡 User Intent: Needs implementation guidance and practical steps")

    # Detect comparison intent
    if any(word in question_lower for word in ["difference", "vs", "versus", "better", "should i"]):
        intents.append("💡 User Intent: Needs comparison and decision guidance")

    # Detect debugging intent
    if any(word in question_lower for word in ["error", "wrong", "fail", "issue", "problem"]):
        intents.append("💡 User Intent: Troubleshooting an issue - provide diagnostics")

    # Detect learning intent
    if any(word in question_lower for word in ["what", "why", "explain", "understanding"]):
        intents.append("💡 User Intent: Learning mode - provide education and context")

    # Detect optimization intent
    if any(word in question_lower for word in ["best", "optimize", "improve", "performance", "efficient"]):
        intents.append("💡 User Intent: Wants best practices and optimization strategies")

    # Add implicit considerations
    implicit = []

    # Payment-related
    if any(word in question_lower for word in ["payment", "charge", "billing", "subscription"]):
        implicit.append("Consider: Security, PCI compliance, error handling, testing")

    # API-related
    if any(word in question_lower for word in ["api", "endpoint", "webhook", "request"]):
        implicit.append("Consider: Authentication, rate limiting, retries, error codes")

    # Frontend-related
    if any(word in question_lower for word in ["frontend", "javascript", "element", "form", "ui"]):
        implicit.append("Consider: User experience, validation, loading states, accessibility")

    # Add context to prompt
    context = ""
    if intents:
        context += "\n" + "\n".join(intents)
    if implicit:
        context += "\n" + "\n".join(implicit)

    return context if context else ""

def build_prompt(question: str, passages: list[str], supercharged: bool = True):
    """
    Main entry point - backwards compatible with original function

    Set supercharged=False to use original restrictive prompt
    """
    if supercharged:
        return build_supercharged_prompt(question, passages, mode="comprehensive")
    else:
        # Original implementation for backwards compatibility
        cites = []
        for i, p in enumerate(passages, 1):
            text = p.strip()
            if len(text) > 1500:
                text = text[:1500] + " ..."
            cites.append(f"[{i}] {text}")
        cite_block = "\n".join(cites) if cites else "[1] No passages provided."

        return f"""{DOCS_ONLY_BASIC}

Question:
{question}

Relevant Passages:
{cite_block}

Instructions:
- Answer using ONLY the Relevant Passages.
- Cite like [1], [2] for each factual assertion.
- If not supported: "Not found in the provided documentation."
Answer:"""

# Example demonstrating the difference
if __name__ == "__main__":
    sample_question = "How do I handle failed payments?"
    sample_passages = [
        "When a payment fails, Stripe sends a payment_intent.payment_failed webhook event...",
        "You can implement retry logic using exponential backoff...",
        "Common failure reasons include insufficient funds, card declined..."
    ]

    print("ORIGINAL PROMPT:")
    print("-" * 50)
    print(build_prompt(sample_question, sample_passages, supercharged=False))

    print("\n\nSUPERCHARGED PROMPT:")
    print("-" * 50)
    print(build_prompt(sample_question, sample_passages, supercharged=True))