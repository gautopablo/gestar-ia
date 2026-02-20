import smtplib
from email.mime.text import MIMEText

SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587

SMTP_USER = "gautop@taranto.com.ar"  # tu usuario
SMTP_PASSWORD = "XXXXX"  # tu contraseña
TO_EMAIL = "gautop@taranto.com.ar"  # podés enviarte a vos mismo


def test_smtp():
    msg = MIMEText("Prueba SMTP desde script Python.")
    msg["Subject"] = "Test SMTP"
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print("✅ Email enviado correctamente.")
    except Exception as e:
        print("❌ Error enviando email:")
        print(e)


if __name__ == "__main__":
    test_smtp()
