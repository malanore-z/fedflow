"""
Templates for reporting
=========================

Some methods for concat html string.
"""

__all__ = [
    "group_template"
]


group_html = """<div style="width: 80%%; margin-left: 10%%">
    <h3>Group %s Finished</h3>
    <p>%d tasks total, %d successful, %d failed.</p>
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


def success_table(datas: list) -> str:
    ret = ["<table border>",
           "<tr><td>task id</td><td>train acc</td><td>val acc</td>",
           "<td>data</td><td>load time</td><td>train time</td></tr>"]
    for taskid, data in datas:
        ret.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
                   (taskid, data["train_acc"], data["val_acc"], data["data"], data["load_time"], data["train_time"]))
    ret.append("</table>")
    return "".join(ret)


def fail_table(datas: list) -> str:
    ret = ["<table border>", "<tr><td>task id</td><td>stage</td><td>message</td></tr>"]
    for taskid, data in datas:
        ret.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (taskid, data["stage"], data["message"]))
    ret.append("</table>")
    return "".join(ret)


def group_template(name: str, result: dict) -> str:
    """
    group report template html.

    :param name: group name
    :param result: group schedule result.
    :return: the html string.
    """
    global group_html
    success_datas = []
    fail_datas = []
    for k, v in result.items():
        if v["type"] == "success":
            success_datas.append((k, v["data"]))
        else:
            fail_datas.append((k, v["data"]))
    return group_html % (name, len(result), len(success_datas), len(fail_datas),
                         success_table(success_datas), fail_table(fail_datas))
