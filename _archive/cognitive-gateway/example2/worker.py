import asyncio
import logging
import os
from dotenv import load_dotenv

from temporalio.client import Client
from temporalio.worker import Worker

from workflows import FinancialAssistantWorkflow

from activities import fetch_transactions, retrieve_context_from_transactions, generate_response

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TEMPORAL_URL = os.getenv("TEMPORAL_SERVER_URL", "localhost:7233")
TASK_QUEUE_NAME = os.getenv("TEMPORAL_TASK_QUEUE", "banking-insight-queue")


async def main():
    """Conecta al cliente y ejecuta el worker."""
    worker = None
    try:
        client = await Client.connect(TEMPORAL_URL)
        logging.info(f"Conectado exitosamente al servidor de Temporal en {TEMPORAL_URL}")

        # Instancia del Worker con las importaciones explícitas
        worker = Worker(
            client,
            task_queue=TASK_QUEUE_NAME,
            workflows=[FinancialAssistantWorkflow],
            activities=[
                fetch_transactions,
                retrieve_context_from_transactions,
                generate_response
            ],
        )

        logging.info(f"👷 Worker iniciado en la cola de tareas '{TASK_QUEUE_NAME}'...")
        await worker.run()

    except Exception as e:
        logging.error(f"Ocurrió un error inesperado durante la ejecución: {e}")
    finally:
        if worker:
            await worker.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nWorker detenido por el usuario.")