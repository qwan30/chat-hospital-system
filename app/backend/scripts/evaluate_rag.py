import asyncio
import json
import uuid

from hospital_ai.core.config import get_settings
from hospital_ai.db.models import User
from hospital_ai.db.session import get_session_factory
from hospital_ai.services.chat import ChatService
from hospital_ai.services.llm import LLMManager
from hospital_ai.services.llm.base import LLMMessage


async def load_dataset(filepath: str):
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)

async def evaluate_with_judge(llm, question: str, response: str, context: str) -> dict[str, float]:
    prompt = f"""You are a clinical AI judge evaluating a RAG chatbot's response.
You must output a JSON object with exactly three keys ("faithfulness", "relevance", "citation_accuracy"), and each value must be a float between 0.0 and 1.0.

Question: {question}
Retrieved Context: {context}
Chatbot Response: {response}

Definitions:
1. faithfulness: 1.0 if the response relies entirely on the retrieved context (no hallucination). 0.0 if it makes up medical claims not in the context.
2. relevance: 1.0 if it answers the question directly. 0.0 if it completely misses the point.
3. citation_accuracy: 1.0 if every factual claim is properly followed by a citation like [E1]. 0.0 if claims lack citations or cite non-existent sources. (For conversational/chitchat or 'no evidence' responses, this can be 1.0 if appropriate).

Output JSON only. Do not wrap it in markdown block quotes.
"""
    messages = [LLMMessage(role="user", content=prompt)]
    try:
        res = await llm.generate(messages)
        text = res.text.strip()
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Error calling judge LLM: {e}")
        return {"faithfulness": 0.0, "relevance": 0.0, "citation_accuracy": 0.0}

async def main():
    settings = get_settings()
    # Ensure we use Gemini for the real evaluation, not stub
    settings.chat_provider = "gemini"
    
    session_factory = get_session_factory()
    manager = LLMManager(settings=settings)
    judge_llm = manager.get()
    
    try:
        dataset = await load_dataset("tests/eval_dataset.json")
    except FileNotFoundError:
        print("Dataset tests/eval_dataset.json not found. Please wait for dataset_engineer to finish.")
        return

    results = []
    print(f"Loaded {len(dataset)} scenarios for evaluation.")

    async with session_factory() as session:
        chat_svc = ChatService(session, settings)
        
        for item in dataset:
            print(f"\nEvaluating: {item['id']} - {item['query']}")
            user = User(id=uuid.uuid4(), email=f"{item['role']}_{uuid.uuid4().hex[:4]}@test.com", role=item['role'], full_name=f"Test {item['role']}")
            session.add(user)
            
            patient_id = None
            if item.get('patient_related', True):
                patient_id = uuid.UUID("20000000-0000-0000-0000-000000000001")
                from hospital_ai.db.models import PatientPermission
                session.add(PatientPermission(user_id=user.id, patient_id=patient_id, scope="read"))
            
            await session.commit()
            
            try:
                ans = await chat_svc.answer(
                    user=user,
                    patient_id=patient_id,
                    question=item['query'],
                    top_k=5,
                    trace_id=str(uuid.uuid4()),
                    ip_address="127.0.0.1"
                )
                response_text = ans.answer
                
                # Mock context for now. In a real system, we'd extract the actual chunks from RAG trace.
                context = "Mock retrieved context string."
                scores = await evaluate_with_judge(judge_llm, item['query'], response_text, context)
                
            except Exception as e:
                response_text = str(e)
                if "User is not authorized" in response_text and "block" in item.get("expected_behavior", "").lower():
                    scores = {"faithfulness": 1.0, "relevance": 1.0, "citation_accuracy": 1.0}
                else:
                    scores = {"faithfulness": 0.0, "relevance": 0.0, "citation_accuracy": 0.0}

            result = {
                "id": item["id"],
                "query": item["query"],
                "response": response_text,
                "scores": scores
            }
            results.append(result)
            print(f"Response: {response_text[:100]}... | Scores: {scores}")

    # Generate Markdown Report
    with open("../../rag_evaluation_report.md", "w", encoding="utf-8") as f:
        f.write("# RAG Evaluation Report\n\n")
        f.write("| ID | Query | Faithfulness | Relevance | Citation Accuracy |\n")
        f.write("|----|-------|--------------|-----------|-------------------|\n")
        
        total_f, total_r, total_c = 0.0, 0.0, 0.0
        
        for r in results:
            s = r["scores"]
            total_f += s.get("faithfulness", 0)
            total_r += s.get("relevance", 0)
            total_c += s.get("citation_accuracy", 0)
            f.write(f"| {r['id']} | {r['query']} | {s.get('faithfulness', 0)} | {s.get('relevance', 0)} | {s.get('citation_accuracy', 0)} |\n")
            
        f.write("\n## Summary\n")
        n = len(results) if results else 1
        f.write(f"- **Avg Faithfulness:** {total_f / n:.2f}\n")
        f.write(f"- **Avg Relevance:** {total_r / n:.2f}\n")
        f.write(f"- **Avg Citation Accuracy:** {total_c / n:.2f}\n")

    print("\nEvaluation complete. Report generated at rag_evaluation_report.md")

if __name__ == "__main__":
    asyncio.run(main())
