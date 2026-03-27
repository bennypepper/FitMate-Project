import httpx
from core.config import settings
from twilio.rest import Client

class WhatsAppClient:
    """
    Sends WhatsApp messages via Twilio Sandbox.
    Sandbox sender: whatsapp:+14155238886
    """
    def __init__(self):
        self.twilio = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}"

    async def send_text_message(self, to_phone: str, text: str):
        """
        to_phone: raw phone number string e.g. '+628xxxxxxxxxx'
        Twilio requires the 'whatsapp:' prefix on both sides.
        """
        # Normalise — Twilio sends 'whatsapp:+628...' as From; strip prefix if present
        clean_to = to_phone.replace("whatsapp:", "")
        
        # Twilio client is synchronous — run in a thread to avoid blocking the event loop
        import asyncio
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.twilio.messages.create(
                from_=self.from_number,
                to=f"whatsapp:{clean_to}",
                body=text,
            )
        )
        return {"sid": message.sid, "status": message.status}

whatsapp_client = WhatsAppClient()
