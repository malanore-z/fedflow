import logging
import os
from email.mime.text import MIMEText
from email.header import Header

from fedflow.config import Config
from fedflow.mail.templates import group_template
from fedflow.mail.send_mail import send_mail


class Mail(object):

    logger = logging.getLogger("fedflow")

    @classmethod
    def send_group_result(cls, name, result: dict):
        html = group_template(name, result)
        message = MIMEText(html, "html", "utf-8")
        message["Subject"] = Header("Fedflow %s report" % name, "utf-8")
        if Config.get_property("smtp.enable"):
            if send_mail(message):
                cls.logger.info("send group report mail.")
            else:
                cls.logger.error("send group report mail failed.")

        reports_dir = os.path.join(Config.get_property("workdir"), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filename = os.path.join(reports_dir, "%s.html" % name)
        with open(filename, "wb") as f:
            f.write(html.encode("utf-8"))
