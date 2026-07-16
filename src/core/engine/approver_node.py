"""
Governance Agent (Approver Node)

This node enforces the Dialectical Synthesis mandate. It invokes the
multi-model consensus evaluator tool. If the evaluation fails, it explicitly
generates a Thesis, Antithesis, and Synthesis before routing the artifact
back to the Maker for remediation.
"""

from typing import Dict, Any
import json
import logging
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.tools.evaluator import evaluate_artifact
from src.core.tools.signer import sign_artifact
from src.core.config import settings
from src.core.ontology import ApproverState

logger = logging.getLogger(__name__)


async def approver_node(state: ApproverState) -> ApproverState:
    """
    LangGraph node for the Governance Agent (Approver).
    """
    user_prompt = state.get("user_prompt", "")
    generated_code = state.get("generated_code", "")
    session_id = state.get("thread_id", "default-session")
    
    logger.info(f"Approver Node executing for session {session_id}")
    
    # Invoke the LCEL Evaluator Tool
    evaluation_result = await evaluate_artifact.ainvoke({
        "user_prompt": user_prompt,
        "generated_code": generated_code,
        "session_id": session_id
    })
    
    if "EVALUATION PASSED" in evaluation_result:
        signature, certificate = "", ""
        
        if settings.REQUIRE_CRYPTOGRAPHIC_SIGNATURE:
            logger.info("Approver Node passed artifact. Proceeding to cryptographic signing...")
            # Epic 10: Cryptographically sign the artifact (PVV)
            pvv = await sign_artifact(generated_code)
            signature = pvv.get("signature", "")
            certificate = pvv.get("certificate", "")
            feedback_msg = "Consensus reached. Artifact approved and signed."
        else:
            logger.info("Approver Node passed artifact. Cryptographic signing is disabled.")
            feedback_msg = "Consensus reached. Artifact approved."
            
        return {
            "status": "APPROVED",
            "approver_feedback": feedback_msg,
            "evaluation_result": evaluation_result,
            "signature": signature,
            "certificate": certificate
        }
        
    # If failed, perform Dialectical Synthesis
    logger.info("Approver Node rejected artifact. Initiating Dialectical Synthesis.")
    
    llm = init_chat_model(model=settings.LLM_MODEL_NAME, temperature=0.2)
    
    dialectical_prompt = f"""
    You are the Governance Agent. The Maker agent's code failed semantic evaluation.
    You must provide actionable feedback to the Maker agent using Dialectical Synthesis.
    
    USER PROMPT: {user_prompt}
    
    GENERATED CODE:
    {generated_code}
    
    EVALUATION FAILURE REASONING:
    {evaluation_result}
    
    Output strictly in the following format:
    
    THESIS: [Explain the intent of the Maker's generated code and why it was proposed]
    ANTITHESIS: [Explain the strongest flaw or missing requirement based on the evaluation]
    SYNTHESIS: [Provide the exact reconciled instructions the Maker must follow to fix the code]
    """
    
    response = await llm.ainvoke([SystemMessage(content=dialectical_prompt)])
    synthesis_feedback = response.content
    
    return {
        "status": "REJECTED",
        "approver_feedback": synthesis_feedback,
        "evaluation_result": evaluation_result
    }
