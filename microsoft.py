import smtplib
import time
import random
import threading
import email.utils
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# TESTING_MODE=True → 10 s delays; False → real delays (30 s between sends, 1 day follow‑ups)
TESTING_MODE = False
initial_gap      = 10 if TESTING_MODE else 30      # seconds between initial emails
followup_delay   = 10 if TESTING_MODE else 86400   # seconds (1 day) before each follow‑up

# Your sender options
SENDER_OPTIONS = [
    {
        "sender_email":    "neal@filldesigngroup.net",
        "sender_password": "Fdg@9874#",
        "smtp_server":     "smtp.office365.com",
        "smtp_port":       587
    },
    {
        "sender_email":    "neal@filldesignprojects.com",
        "sender_password": "Fdg@9874#",
        "smtp_server":     "smtp.office365.com",
        "smtp_port":       587
    },
    {
        "sender_email":    "neal@filldesignprojects.website",
        "sender_password": "Fdg@9874#",
        "smtp_server":     "smtp.office365.com",
        "smtp_port":       587
    }
]

def get_random_sender():
    return random.choice(SENDER_OPTIONS)

def spin_email_template(person_name, company, is_followup=False, followup_number=None):
    greetings = [f"Hi {person_name},", f"Hello {person_name},", f"Dear {person_name},"]
    sentence1 = random.choice([
        "I see you booked your new domain, marking an important step toward establishing a strong online presence.",
        "I noticed you secured your new domain—an essential move toward building a reliable online identity.",
        "I noticed you secured your domain. This marks the beginning of your online journey."
    ])
    sentence2 = random.choice([
        "In the past six months, we’ve worked with several businesses to build websites, improve their search performance, and refine their social media presence. Consider how a well-designed digital platform can support your goals.",
        "Over the past six months, we’ve assisted a number of companies with website design, search optimization, and social media strategy. Think about how a customized digital solution could benefit your business.",
        "Recently, we’ve helped several businesses develop websites, enhance their search performance, and improve their social media efforts. Imagine a digital solution that aligns with your business needs."
    ])
    sentence3 = random.choice([
        "I’m contacting you personally to share how our services may be of benefit. Please take a moment to watch the brief video I recorded, which explains our approach.",
        "I’m contacting you directly to share more about our services. I’ve prepared a brief video introduction outlining our process.",
        "I’m reaching out personally to share how our services may help. I’ve recorded a short video to introduce myself and explain our approach."
    ])
    extra = f"\nThis is follow-up #{followup_number}. Just checking in regarding my previous email." \
            if is_followup and followup_number else ""
    loom_link = "https://www.loom.com/share/1915f664b7f145f193d7b0fd6873ecb1"

    text = f"""{random.choice(greetings)}

{sentence1}

{sentence2}

{sentence3}

{extra}

{loom_link}

Looking forward to hearing from you.

Best regards,
Neal
https://filldesigngroup.com/
"""
    html = f"""\
<html><body>
  <p>{random.choice(greetings)}</p>
  <p>{sentence1}</p>
  <p>{sentence2}</p>
  <p>{sentence3}</p>
  {f"<p>{extra}</p>" if extra else ""}
  <div>
    <a href="{loom_link}">
      <img style="max-width:300px;" src="https://cdn.loom.com/sessions/thumbnails/1915f664b7f145f193d7b0fd6873ecb1-12ee91ac978e3ba5-full-play.gif" alt="Watch Video">
    </a>
  </div>
  <p>Looking forward to hearing from you.<br>Best regards,<br>Neal<br>
     <a href="https://filldesigngroup.com/">Fill Design Group</a></p>
</body></html>
"""
    return text, html

def choose_subject(company):
    return random.choice([
        "Question for {Company}",
        "See this for {Company}",
        "Quick Question for {Company}"
    ]).format(Company=company)

def check_reply(recipient_email):
    # TODO: integrate real reply-checking via IMAP/CRM
    return False

def send_email(to_addr, name, company, sender, is_followup=False, followup_number=None, orig_msg_id=None, orig_subject=None):
    text, html = spin_email_template(name, company, is_followup, followup_number)
    msg = MIMEMultipart('alternative')
    msg['From'] = sender['sender_email']
    msg['To']   = to_addr
    if is_followup:
        msg['Subject'] = "Re: " + orig_subject
        msg['In-Reply-To'] = orig_msg_id
        msg['References']  = orig_msg_id
    else:
        subject = choose_subject(company)
        msg['Subject'] = subject
    msg_id = email.utils.make_msgid()
    if not is_followup:
        msg['Message-ID'] = msg_id

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(sender['smtp_server'], sender['smtp_port'], timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender['sender_email'], sender['sender_password'])
            server.sendmail(sender['sender_email'], to_addr, msg.as_string())
            action = "Follow-up" if is_followup else "Initial"
            num    = f" #{followup_number}" if is_followup else ""
            print(f"{action}{num} email sent to {to_addr} from {sender['sender_email']}")
    except Exception as e:
        print(f"Error sending {'follow-up' if is_followup else 'initial'} email to {to_addr}: {e}")

    return msg_id, msg['Subject']

def followup_scheduler(to_addr, name, company, sender, orig_msg_id, orig_subject):
    # Wait for follow-up #1
    time.sleep(followup_delay)
    if not check_reply(to_addr):
        _, _ = send_email(to_addr, name, company, sender, True, 1, orig_msg_id, orig_subject)
    else:
        return
    # Wait for follow-up #2
    time.sleep(followup_delay)
    if not check_reply(to_addr):
        _, _ = send_email(to_addr, name, company, sender, True, 2, orig_msg_id, orig_subject)

def send_emails(xlsx_path):
    df = pd.read_excel(xlsx_path, engine='openpyxl')  # requires openpyxl
    for _, row in df.iterrows():
        company = row['company']
        name    = row['name']
        email   = row['email']
        print(f"Processing: {company} | {name} | {email}")

        sender = get_random_sender()
        msg_id, subject = send_email(email, name, company, sender)
        # schedule follow-ups in background
        threading.Thread(
            target=followup_scheduler,
            args=(email, name, company, sender, msg_id, subject)
        ).start()

        time.sleep(initial_gap)

if __name__ == "__main__":
    send_emails("test Email.xlsx")
