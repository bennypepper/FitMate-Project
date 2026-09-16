import asyncio
import logging
from core.config import settings
from twilio.rest import Client

logger = logging.getLogger("fitmate.whatsapp")

class WhatsAppClient:
    """
    Sends WhatsApp messages via Twilio Sandbox.
    Sandbox sender: whatsapp:+14155238886
    """
    def __init__(self):
        self.twilio = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}"

    async def send_text_message(self, to_phone: str, text: str, timeout: float = 10.0) -> dict:
        """
        to_phone: raw phone number string e.g. '+628xxxxxxxxxx'
        Twilio requires the 'whatsapp:' prefix on both sides.
        Bounded by timeout (default 10s).
        """
        if not self.twilio:
            logger.warning("[WhatsApp] Twilio credentials not configured. Message skipped.")
            return {"sid": "dummy_sid_unconfigured", "status": "skipped"}

        clean_to = to_phone.replace("whatsapp:", "")

        loop = asyncio.get_running_loop()
        try:
            message = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.twilio.messages.create(
                        from_=self.from_number,
                        to=f"whatsapp:{clean_to}",
                        body=text,
                    )
                ),
                timeout=timeout
            )
            return {"sid": message.sid, "status": message.status}
        except asyncio.TimeoutError:
            logger.error(f"[WhatsApp] Twilio API call timed out after {timeout}s for {clean_to}")
            raise TimeoutError(f"WhatsApp delivery timed out after {timeout} seconds")
        except Exception as exc:
            logger.error(f"[WhatsApp] Twilio send failed: {exc}", exc_info=True)
            raise

whatsapp_client = WhatsAppClient()
