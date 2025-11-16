"""
Workflow Orchestrator - LangGraph-based agentic workflow
"""
import json
import logging
from typing import TypedDict, Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import os
import networkx as nx

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State passed through the workflow"""
    change_description: str
    affected_files: List[str]
    repo_id: str
    branch: str
    dependency_graph: Optional[Dict[str, Any]]
    retrieved_context: List[Dict[str, Any]]
    impact_analysis: Dict[str, Any]
    test_plan: Dict[str, Any]
    criticality_scores: Dict[str, float]
    final_report: Dict[str, Any]
    error: Optional[str]
    workflow_metadata: Dict[str, Any]


class WorkflowOrchestrator:
    """Orchestrates the impact analysis workflow using LangGraph"""
    
    def __init__(self, rag_pipeline=None):
        """
        Initialize orchestrator
        
        Args:
            rag_pipeline: RAG pipeline instance for context retrieval
        """
        self.rag_pipeline = rag_pipeline
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.compiled_workflow = None
    
    def build_workflow(self):
        """
        Build the LangGraph workflow
        
        Returns:
            Compiled workflow graph
        """
        try:
            workflow = StateGraph(WorkflowState)
            
            # Define nodes
            workflow.add_node("query_planner", self.plan_queries)
            workflow.add_node("dependency_analyzer", self.analyze_dependencies)
            workflow.add_node("rag_retriever", self.retrieve_context)
            workflow.add_node("impact_scorer", self.score_impact)
            workflow.add_node("test_planner", self.plan_tests)
            workflow.add_node("report_generator", self.generate_report)
            
            # Set entry point
            workflow.set_entry_point("query_planner")
            
            # Define edges
            # From query_planner, split to dependency_analyzer and rag_retriever (parallel)
            workflow.add_edge("query_planner", "dependency_analyzer")
            workflow.add_edge("query_planner", "rag_retriever")
            
            # Both converge at impact_scorer
            workflow.add_edge("dependency_analyzer", "impact_scorer")
            workflow.add_edge("rag_retriever", "impact_scorer")
            
            # Sequential path after impact_scorer
            workflow.add_edge("impact_scorer", "test_planner")
            workflow.add_edge("test_planner", "report_generator")
            
            # End after report generation
            workflow.add_edge("report_generator", END)
            
            # Compile workflow
            self.compiled_workflow = workflow.compile()
            
            logger.info("Workflow built successfully")
            return self.compiled_workflow
            
        except Exception as e:
            logger.error(f"Error building workflow: {str(e)}")
            raise
    
    def plan_queries(self, state: WorkflowState) -> WorkflowState:
        """
        Query Planner - Parse and plan the analysis
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"Planning queries for: {state['change_description'][:100]}")
            
            prompt = f"""Analyze this code change and identify what needs to be analyzed:

Change: {state['change_description']}

Provide a JSON response with:
1. key_areas: List of code areas affected
2. analysis_priorities: Priority levels (HIGH/MEDIUM/LOW)
3. testing_requirements: What needs to be tested
4. risks: Identified risks"""
            
            response = self.llm.invoke(prompt)
            
            try:
                plan = json.loads(response.content if hasattr(response, 'content') else str(response))
            except json.JSONDecodeError:
                plan = {"raw_response": response.content if hasattr(response, 'content') else str(response)}
            
            state['workflow_metadata'] = {
                **state.get('workflow_metadata', {}),
                "query_plan": plan
            }
            
            logger.info("Query planning completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in query planner: {str(e)}")
            state['error'] = f"Query planning failed: {str(e)}"
            return state
    
    def analyze_dependencies(self, state: WorkflowState) -> WorkflowState:
        """
        Dependency Analyzer - Analyze graph structure
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            logger.info("Analyzing dependencies...")
            
            # If dependency_graph is provided, analyze it
            impact_analysis = {
                "affected_components": state.get('affected_files', []),
                "analysis_type": "dependency_graph",
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }
            
            if state.get('dependency_graph'):
                # Reconstruct graph and find affected nodes
                graph = nx.node_link_graph(state['dependency_graph'])
                
                affected = set()
                for file in state.get('affected_files', []):
                    if file in graph:
                        # Get descendants and ancestors
                        affected.update(nx.descendants(graph, file))
                        affected.update(nx.ancestors(graph, file))
                
                impact_analysis['affected_components'] = list(affected)
                impact_analysis['impact_count'] = len(affected)
            
            state['impact_analysis'] = impact_analysis
            logger.info(f"Found {len(state['impact_analysis'].get('affected_components', []))} affected components")
            return state
            
        except Exception as e:
            logger.error(f"Error in dependency analyzer: {str(e)}")
            state['error'] = f"Dependency analysis failed: {str(e)}"
            return state
    
    def retrieve_context(self, state: WorkflowState) -> WorkflowState:
        """
        RAG Retriever - Retrieve relevant code context
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            logger.info("Retrieving context...")
            
            if not self.rag_pipeline:
                logger.warning("RAG pipeline not available, skipping context retrieval")
                state['retrieved_context'] = []
                return state
            
            # Retrieve context based on change description and affected files
            query = f"{state['change_description']} {' '.join(state.get('affected_files', [])[:5])}"
            context = self.rag_pipeline.retrieve_context(query, k=10)
            
            state['retrieved_context'] = context
            logger.info(f"Retrieved {len(context)} context documents")
            return state
            
        except Exception as e:
            logger.error(f"Error in RAG retriever: {str(e)}")
            state['retrieved_context'] = []
            return state
    
    def score_impact(self, state: WorkflowState) -> WorkflowState:
        """
        Impact Scorer - Score criticality and risk
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            logger.info("Scoring impact...")
            
            # Prepare scoring prompt
            affected_components = state.get('impact_analysis', {}).get('affected_components', [])
            context_summary = f"Retrieved {len(state.get('retrieved_context', []))} context documents"
            
            prompt = f"""Based on the analysis, score the impact of this change:

Affected Components: {len(affected_components)}
Context Summary: {context_summary}

Provide impact scores (0-1) for:
1. criticality_score: How critical are the affected components?
2. risk_score: What's the risk level of this change?
3. testing_scope: What % of tests need to be run?

Response format: JSON with numeric scores"""
            
            response = self.llm.invoke(prompt)
            
            try:
                scores = json.loads(response.content if hasattr(response, 'content') else str(response))
                # Ensure numeric values
                state['criticality_scores'] = {
                    'criticality': float(scores.get('criticality_score', 0.5)),
                    'risk': float(scores.get('risk_score', 0.5)),
                    'testing_scope': float(scores.get('testing_scope', 0.5))
                }
            except (json.JSONDecodeError, ValueError):
                state['criticality_scores'] = {
                    'criticality': 0.5,
                    'risk': 0.5,
                    'testing_scope': 0.5
                }
            
            logger.info(f"Impact scored: {state['criticality_scores']}")
            return state
            
        except Exception as e:
            logger.error(f"Error in impact scorer: {str(e)}")
            state['criticality_scores'] = {'criticality': 0.5, 'risk': 0.5, 'testing_scope': 0.5}
            return state
    
    def plan_tests(self, state: WorkflowState) -> WorkflowState:
        """
        Test Planner - Generate test recommendations
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            logger.info("Planning tests...")
            
            affected_count = len(state.get('impact_analysis', {}).get('affected_components', []))
            criticality = state.get('criticality_scores', {}).get('criticality', 0.5)
            
            prompt = f"""Generate a test plan for this code change:

Affected Components: {affected_count}
Criticality Score: {criticality}
Change: {state['change_description'][:500]}

Provide test recommendations:
1. unit_tests: List of unit tests to run
2. integration_tests: Integration tests needed
3. smoke_tests: Critical smoke tests
4. priority: Test execution priority

Response format: JSON"""
            
            response = self.llm.invoke(prompt)
            
            try:
                test_plan = json.loads(response.content if hasattr(response, 'content') else str(response))
            except json.JSONDecodeError:
                test_plan = {
                    "unit_tests": [f"test_affected_component_{i}" for i in range(min(5, affected_count))],
                    "integration_tests": ["integration_test_main_flow"],
                    "smoke_tests": ["smoke_test_critical_paths"]
                }
            
            state['test_plan'] = test_plan
            logger.info(f"Test plan generated with {len(test_plan.get('unit_tests', []))} unit tests")
            return state
            
        except Exception as e:
            logger.error(f"Error in test planner: {str(e)}")
            state['test_plan'] = {"error": str(e)}
            return state
    
    def generate_report(self, state: WorkflowState) -> WorkflowState:
        """
        Report Generator - Create final analysis report
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final report
        """
        try:
            logger.info("Generating final report...")
            
            report = {
                "repo_id": state.get('repo_id'),
                "branch": state.get('branch'),
                "change_description": state.get('change_description'),
                "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
                "impact_analysis": state.get('impact_analysis', {}),
                "criticality_scores": state.get('criticality_scores', {}),
                "test_plan": state.get('test_plan', {}),
                "error": state.get('error')
            }
            
            state['final_report'] = report
            logger.info("Final report generated successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in report generator: {str(e)}")
            state['final_report'] = {"error": str(e)}
            return state
    
    async def execute_workflow(self, initial_state: WorkflowState) -> WorkflowState:
        """
        Execute the compiled workflow
        
        Args:
            initial_state: Initial workflow state
            
        Returns:
            Final workflow state with all results
        """
        try:
            if not self.compiled_workflow:
                self.build_workflow()
            
            logger.info("Executing workflow...")
            
            # Invoke the workflow
            result = self.compiled_workflow.invoke(initial_state)
            
            logger.info("Workflow execution completed")
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            initial_state['error'] = f"Workflow failed: {str(e)}"
            return initial_state
