from temporalio import workflow
from datetime import timedelta
from temporalio.common import RetryPolicy

from activities import fetch_transactions, retrieve_context_from_transactions, generate_response

@workflow.defn
class FinancialAssistantWorkflow:
    @workflow.run
    async def run(self, user_id: str, question: str) -> str:
        """Orquesta un flujo de RAG simple y robusto."""
        
        default_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),  # Primer reintento después de 1 segundo
            backoff_coefficient=2.0,                # Duplica el intervalo en cada reintento
            maximum_interval=timedelta(minutes=1),  # Intervalo máximo entre reintentos de 1 minuto
            maximum_attempts=5,                     # Máximo de 5 intentos (1 original + 4 reintentos)
            non_retryable_error_types=["ValueError"] # Errores que no deben reintentarse
        )

        # Paso 1: Obtener transacciones
        transactions = await workflow.execute_activity(
            fetch_transactions, 
            user_id, 
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=default_retry_policy 
        )

        # Paso 2: Obtener contexto relevante
        relevant_context = await workflow.execute_activity(
            retrieve_context_from_transactions, 
            args=[transactions, question], 
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Paso 3: Generar la respuesta final
        final_answer = await workflow.execute_activity(
            generate_response, 
            args=[relevant_context, question], 
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        return final_answer