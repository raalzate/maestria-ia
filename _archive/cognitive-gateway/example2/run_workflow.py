import asyncio
import os
import argparse  
import logging
from dotenv import load_dotenv

from temporalio.client import Client
from temporalio.exceptions import ApplicationError

from workflows import FinancialAssistantWorkflow

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 2. Se usa la misma configuración del .env que el worker
TEMPORAL_URL = os.getenv("TEMPORAL_SERVER_URL", "localhost:7233")
TASK_QUEUE_NAME = os.getenv("TEMPORAL_TASK_QUEUE", "banking-insight-queue")


async def main(args):
    """Conecta al cliente y ejecuta el workflow con los argumentos proporcionados."""
    try:
        client = await Client.connect(TEMPORAL_URL)
        
        logging.info(f"▶️  Iniciando workflow con user_id='{args.user_id}' y pregunta='{args.question}'...")

        # 4. Usamos execute_workflow para una ejecución más simple
        result = await client.execute_workflow(
            FinancialAssistantWorkflow.run,
            args=[args.user_id, args.question],
            id=f"financial-assistant-workflow-{args.user_id}-{asyncio.get_event_loop().time()}",
            task_queue=TASK_QUEUE_NAME,
        )

        logging.info(f"\n✅ Respuesta del Asistente:\n\n{result}\n")

    # 3. Manejo de errores específico si el workflow falla
    except ApplicationError as e:
        logging.error(f"❌ El workflow ha fallado: {e.message}")
        logging.error(f"   Tipo de error: {e.type}")
    except Exception as e:
        logging.error(f"❌ Ocurrió un error inesperado al conectar o ejecutar el workflow: {e}")


if __name__ == "__main__":
    # 1. Se define cómo aceptar argumentos desde la línea de comandos
    parser = argparse.ArgumentParser(description="Inicia el workflow de asistente financiero.")
    parser.add_argument(
        "--user-id",
        default="user-123",
        help="El ID del usuario para el cual ejecutar el workflow."
    )
    parser.add_argument(
        "--question",
        default="¿Cuál fue mi depósito más grande y en qué gasté más dinero?",
        help="La pregunta a realizar al asistente financiero."
    )
    
    cli_args = parser.parse_args()
    asyncio.run(main(cli_args))