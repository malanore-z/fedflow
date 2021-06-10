import getpass
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from fedflow.config import Config


def __format_addr(name, addr):
    return formataddr((Header(name, "utf-8").encode(), addr))


def send_mail(message: MIMEText):
    try:
        server_host = Config.get_property("smtp.server-host")
        server_port = Config.get_property("smtp.server-port")
        user = Config.get_property("smtp.user")
        password = Config.get_property("smtp.password")
        receiver = Config.get_property("smtp.receiver")

        if None in [server_host, server_port, user, password, receiver] or \
                "" in [server_host, server_port, user, password, receiver]:
            return True

        send_from = __format_addr("noreply", user)
        send_to = __format_addr(getpass.getuser(), receiver)

        message["From"] = send_from
        message["To"] = send_to

        smtp = smtplib.SMTP(server_host, server_port)
        smtp.login(user, password)
        smtp.sendmail(user, [receiver, ], message.as_string())
        smtp.quit()
        return True
    except Exception as e:
        print(e)


if __name__ == "__main__":
    group_html = """<div style="width: 80%%; margin-left: 10%%">
        <h3>Group #1 Finished</h3>
        <p>20 tasks total, 18 successful, 2 failed.</p>
        <HR style="FILTER: alpha(opacity=100,finishopacity=0,style=1)" width="100%%" color=#987cb9 SIZE=3>
        <div>
            <p>Successful:</p>
            %s
        </div>
        <div>
            <p>Exception:</p>
            %s
        </div>
    </div>"""
    message = MIMEText(group_html, "html", "utf-8")
    message["Subject"] = "TEST"
    print(send_mail(message))
