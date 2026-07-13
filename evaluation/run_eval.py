import os
import sys
import json
import logging
import asyncio
from datasets import Dataset

# Set up backend import paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

# Set environment keys for local execution
from app.core.config import settings
os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

from app.agents.graph import app_graph
from app.services.vector_db import VectorDBService
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_evaluation():
    logger.info("==================================================")
    # 1. Ingest test data into Vector DB to ensure successful retrieval context
    logger.info("Initializing Vector database and ingesting evaluation documents...")
    vector_db = VectorDBService(collection_name="eval_enterprise_rag")
    
    # Read test dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "test_dataset.json")
    with open(dataset_path, "r") as f:
        test_data = json.load(f)
        
    chunks = [item["ground_truth"] for item in test_data]
    metadata = [{"doc_name": f"eval_doc_{i}.pdf", "page_number": i + 1} for i, _ in enumerate(test_data)]
    
    # Upsert test documents
    success = vector_db.upsert_documents(chunks, metadata)
    if not success:
        logger.error("Failed to ingest test documents. Exiting evaluation.")
        return
    logger.info("Evaluation documents ingested successfully.")
    
    # Override vector DB reference inside the agent graph service to use eval collection
    import app.agents.graph as graph_module
    graph_module.vector_db = vector_db
    
    # 2. Run agent workflow to collect answers and retrieved contexts
    logger.info("\nRunning queries through Multi-Agent RAG workflow...")
    
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []
    
    for item in test_data:
        question_text = item["question"]
        ground_truth_text = item["ground_truth"]
        
        logger.info(f"Querying: '{question_text}'")
        
        initial_state = {
            "messages": [HumanMessage(content=question_text)],
            "query": question_text,
            "retrieved_contexts": [],
            "draft_response": "",
            "route": "",
            "verification_score": 0.0,
            "verification_reasoning": "",
            "verification_attempts": 0
        }
        
        # Invoke compiled LangGraph synchronously
        try:
            result_state = app_graph.invoke(initial_state)
            
            answer = result_state.get("draft_response", "No answer generated.")
            retrieved_contexts = [ctx.get("content", "") for ctx in result_state.get("retrieved_contexts", [])]
            
            questions.append(question_text)
            answers.append(answer)
            contexts_list.append(retrieved_contexts)
            ground_truths.append(ground_truth_text)
            
            logger.info(f"Answer: {answer[:60]}...")
            logger.info(f"Contexts retrieved: {len(retrieved_contexts)}")
        except Exception as e:
            logger.error(f"Error querying agent: {e}")
            
    # 3. Compile evaluation dataset
    logger.info("\nCompiling evaluation dataset for Ragas...")
    data_dict = {
        "question": questions,
        "contexts": contexts_list,
        "answer": answers,
        "ground_truth": ground_truths
    }
    
    dataset = Dataset.from_dict(data_dict)
    
    # 4. Configure Ragas with Gemini LLM for evaluations
    logger.info("Initializing Gemini evaluation LLM model...")
    eval_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.0,
        google_api_key=settings.GEMINI_API_KEY
    )
    
    # Bind the evaluation model to metrics
    faithfulness.llm = eval_llm
    answer_relevance.llm = eval_llm
    
    # 5. Execute Ragas Evaluation
    logger.info("Executing Ragas metrics calculations...")
    try:
        results = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevance],
            llm=eval_llm
        )
        
        logger.info("\n================ EVALUATION SUMMARY ================")
        print(results)
        logger.info("====================================================")
        
        # Write results to markdown file
        summary_path = os.path.join(os.path.dirname(__file__), "eval_summary.md")
        with open(summary_path, "w") as f:
            f.write("# Offline Evaluation Summary Report\n\n")
            f.write("Generated using the Ragas Evaluation Framework and Google Gemini 2.5 Flash.\n\n")
            f.write("## Overall Metrics Scores\n\n")
            for metric, score in results.items():
                f.write(f"- **{metric.capitalize()}**: {score:.4f}\n")
            f.write("\n## Query-by-Query Detailed Logs\n\n")
            
            df = results.to_pandas()
            for idx, row in df.iterrows():
                f.write(f"### Query {idx + 1}: {row['question']}\n\n")
                f.write(f"- **Reference Ground Truth**: {row['ground_truth']}\n")
                f.write(f"- **Generated Response**: {row['answer']}\n")
                f.write(f"- **Faithfulness Score**: {row['faithfulness']:.4f}\n")
                f.write(f"- **Answer Relevance Score**: {row['answer_relevance']:.4f}\n\n")
                f.write("---\n\n")
                
        logger.info(f"Successfully compiled evaluation summary report to {summary_path}")
        
    except Exception as e:
        logger.error(f"Ragas evaluation run encountered an error: {e}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
