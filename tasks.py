import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal, User, Message
from datetime import datetime, timedelta

logger = logging.getLogger("tasks")
scheduler = AsyncIOScheduler()

async def notify_inactive_students():
    """
    Rotina que busca alunos que não interagiram nas últimas 24h
    e 'simula' o envio de um exercício, flashcards pendentes ou notificação de retenção.
    """
    logger.info("⏰ [Job Background] Iniciando verificação de alunos inativos...")
    db = SessionLocal()
    try:
        # Define o limiar de inatividade (ex: 24 horas - reduzido para 1h na prática como ex)
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        users = db.query(User).all()
        
        for user in users:
            # Buscar a última mensagem desse usuário
            last_msg_query = (
                db.query(Message)
                .filter(Message.role == 'user')
                .filter(Message.session.has(user_id=user.id))
                .order_by(Message.created_at.desc())
                .first()
            )
            
            # Se não conversou recentemente
            if not last_msg_query or last_msg_query.created_at < yesterday:
                logger.info(f"📬 [Notificação] O aluno '{user.username}' não pratica há mais de 24h.")
                
                # Resgatar profile para verificar se tem flashcards
                profile = user.study_profile
                flashcards_info = ""
                if profile and profile.flashcards:
                    total_fc = len(profile.flashcards)
                    flashcards_info = f" Você possui {total_fc} flashcards aguardando revisão!"
                
                # Simular o envio de um email/push nativo:
                mensagem_simulada = (
                    f"Hello {user.username}! Let's practice some English today?"
                    f"{flashcards_info}"
                )
                logger.info(f"📡 SIMULANDO ENVIO: {mensagem_simulada}")
                
    except Exception as e:
        logger.error(f"Erro na tarefa de notificação: {e}")
    finally:
        db.close()

def start_scheduler():
    """Inicia o agendador de tarefas em background."""
    # Para propósitos de demonstração, dispararemos a verificação a cada 60 minutos
    # Em produção usaríamos cron. CronTrigger(hour=10, minute=0) (TODO O DIA AS 10H)
    scheduler.add_job(notify_inactive_students, trigger='interval', minutes=60)
    scheduler.start()
    logger.info("⏱️ APScheduler (Background Worker) acoplado e rolando lindamente.")
