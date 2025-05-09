import pandas as pd
import time
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import random
import os

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# CONFIG
XLSX_PATH      = "test Email.xlsx"
INITIAL_GAP    = 60                       # seconds between initial emails
FOLLOWUP_DELAY = timedelta(days=1)        # 1 day
SENDER = {
    "sender_email":    "neal@filldesignprojects.com",
    "sender_password": "Fdg@9874#",
    "smtp_server":     "smtp.office365.com",
    "smtp_port":       587
}

def spin_email_template(person_name, company, is_followup=False, followup_number=None):
    greetings = [f"Hi {person_name},", f"Hello {person_name},", f"Dear {person_name},"]
    s1 = random.choice([
        "We have worked with over 49+ companies in the past 6 Months.",
        "In the last half-year, we’ve helped more than 49 companies achieve their goals.",
        "Over the past six months, we’ve collaborated with over 49 organizations."
    ])
    s2 = random.choice([
        "Think there might be a fun way to combine forces—nothing formal, just a quick brainstorm. Got 10 minutes next week for a quick meeting? Let me know what your calendar looks like!",
        "I’d love to brainstorm together—nothing formal, just a quick chat. Got 10 minutes next week? Let me know what your calendar looks like!",
        "Think we could have a fun brainstorm—no agenda, just 10 minutes to explore ideas. What time next week works for you?"
    ])
    s3 = random.choice([
        "I’m contacting you personally to share how our services may be of benefit. Please take a moment to watch the brief video I recorded, which explains our approach.",
        "I’m contacting you directly to share more about our services. I’ve prepared a brief video introduction outlining our process.",
        "I’m reaching out personally to share how our services may help. I’ve recorded a short video to introduce myself and explain our approach."
    ])
    greeting = random.choice(greetings)
    extra = (f"\nThis is follow-up #{followup_number}. Just checking in regarding my previous email."
             if is_followup and followup_number else "")
    loom_link = "https://www.loom.com/share/42b0600a660d4da7be729cfbb3fe1f64"

    text = f"""{greeting}

{s1}

{s2}

{s3}

{extra}

{loom_link}

Looking forward to hearing from you.

Best regards,
Neal
https://filldesigngroup.com/
"""
    html = f"""\
<html><body>
  <p>{greeting}</p>
  <p>{s1}</p><p>{s2}</p><p>{s3}</p>
  {f"<p>{extra}</p>" if extra else ""}
  <div><a href="{loom_link}">
    <img style="max-width:300px;"
         src="https://cdn.loom.com/sessions/thumbnails/42b0600a660d4da7be729cfbb3fe1f64-06d77ce33079aa2b-full-play.gif"
         alt="Watch Video"></a></div>
  <p>Looking forward to hearing from you.<br>
     Best regards,<br>
     Neal<br>
     <a href="https://filldesigngroup.com/">Fill Design Group</a>
  </p>
</body></html>
"""
    return text, html

def choose_subject(company):
    return random.choice([
        "Question for {Company}",
        "See this for {Company}",
        "Quick Question for {Company}"
    ]).format(Company=company)

def send_email(to_addr, name, company,
               is_followup=False, followup_number=None,
               orig_msg_id=None, orig_subject=None):
    text, html = spin_email_template(name, company, is_followup, followup_number)
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER["sender_email"]
    msg["To"]   = to_addr

    if is_followup:
        msg["Subject"]     = "Re: " + orig_subject
        msg["In-Reply-To"] = orig_msg_id
        msg["References"]  = orig_msg_id
    else:
        msg["Subject"] = choose_subject(company)

    msg_id = email.utils.make_msgid()
    if not is_followup:
        msg["Message-ID"] = msg_id

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SENDER["smtp_server"], SENDER["smtp_port"], timeout=10) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER["sender_email"], SENDER["sender_password"])
        server.sendmail(SENDER["sender_email"], to_addr, msg.as_string())

    kind = f"Follow-up #{followup_number}" if is_followup else "Initial"
    print(f"[{datetime.utcnow()}] {kind} email sent to {to_addr}")
    return msg_id, msg["Subject"]

def main():
    if not os.path.exists(XLSX_PATH):
        print(f"ERROR: '{XLSX_PATH}' not found")
        return

    df = pd.read_excel(XLSX_PATH, engine="openpyxl")
    now = datetime.utcnow()

    # Coerce sent_time to datetime dtype
    if "sent_time" in df.columns:
        df["sent_time"] = pd.to_datetime(df["sent_time"], errors="coerce")
    else:
        df["sent_time"] = pd.NaT

    # Ensure follow-up flags exist
    for col in ("followup1_sent", "followup2_sent"):
        if col not in df:
            df[col] = False

    changed = False

    # 1) Initial sends
    for idx, row in df.iterrows():
        if pd.isna(row["sent_time"]):
            msg_id, subject = send_email(
                row["email"], row["name"], row["company"],
                False, None, None, None
            )
            sent_ts = datetime.utcnow()
            df.at[idx, "sent_time"]   = sent_ts
            df.at[idx, "Message-ID"]  = msg_id
            df.at[idx, "Subject"]     = subject
            changed = True
            time.sleep(INITIAL_GAP)

    # 2) Follow-up #1 (after 1 day)
    for idx, row in df.iterrows():
        sent = row["sent_time"]
        if not row.get("followup1_sent") and pd.notna(sent) and now - sent >= FOLLOWUP_DELAY:
            msg_id, _ = send_email(
                row["email"], row["name"], row["company"],
                True, 1, row["Message-ID"], row["Subject"]
            )
            df.at[idx, "followup1_sent"] = True
            changed = True

    # 3) Follow-up #2 (after 2 days)
    for idx, row in df.iterrows():
        sent = row["sent_time"]
        if not row.get("followup2_sent") and pd.notna(sent) and now - sent >= (FOLLOWUP_DELAY * 2):
            msg_id, _ = send_email(
                row["email"], row["name"], row["company"],
                True, 2, row["Message-ID"], row["Subject"]
            )
            df.at[idx, "followup2_sent"] = True
            changed = True

    if changed:
        df.to_excel(XLSX_PATH, index=False)
        print(f"[{datetime.utcnow()}] '{XLSX_PATH}' updated.")
    else:
        print("No actions needed.")

if __name__ == "__main__":
    main()
