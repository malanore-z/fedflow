配置
==============

Fedflow的配置参数有很多项，可以使用配置文件的方式，也可以在代码中修改参数。

配置方式
--------

#. 使用配置文件

    ``python -m fedflow generate-config``

    在终端执行以上指令可以在当前文件夹下生成一个config.yaml文件，修改此文件即可。

    Fedflow在执行的时候会尝试在当前文件夹下查找config.yaml文件，如果找到就会使用此文件中的配置，否则使用默认配置文件。

#. 在运行中修改配置

    .. code:: python

        from fedflow.config import Config

        Config.set_property("workdir", "work")
        Config.set_property("utilization-limit.memory", 0.9)

    通过使用 ``fedflow.config.Config#set_property`` 方法，可以修改单个参数。

参数介绍
--------

.. code:: yaml

    # Fedflow 配置示例
    # Fedflow 支持以下字节单位:
    #   B(b), KB(b), MB(b), GB(b), TB(b)
    # 在大多数情况下，推荐使用'(K/M/G/T)B'而不是'(K/M/G/T)b'，并且如果单位是'B'， 可以省略。

    # 在Fedflow运行过程中，所有的硬盘读写操作都在workdir中进行。
    # 默认情况下， workdir是res文件夹
    # 如果workdir不存在，运行中会自动创建，如果workdir存在，不会清空，但是会覆盖同名文件。
    workdir: 'res'

    # 是否开启debug模式，在debug模式下，会记录更详细的日志
    debug: false

    # 你可以指定一个GPU选择优先级， Fedflow会根据优先级选择GPU设备
    gpu-priority:
      stratety: 'TOTAL-MEM'  # PCI, TOTAL-MEM, REMAIN-MEM, PERFORMANCE
      reverse: false  # 是否逆序

    utilization-limit:  # 系统资源的最大利用率，当前利用率超出最大利用率的时候，Fedflow会停止运行新任务
      cpu: 0.8  # 所有逻辑CPU的平均利用率
      memory: 0.8  # 系统内存的最大利用率
      cuda-memory: 0.8  # 每个显卡的显存最大利用率

    remain-limit: # 最低保留的系统资源
      memory: '4GB'
      cuda-memory: '2GB'

    task:   # 任务相关的参数
      directory-grouping: true  # 是否为每个任务组创建文件夹， 如果为true，则每个任务组单独创建文件夹，否则，所有任务的文件夹都组织在workdir下
      allow-duplicate-id: true  # 是否允许任务id重复， 同组的任务id不允许重复，如果此项参数为true，允许全局任务id重复

    scheduler:  # 任务调度相关的参数
      default-memory: '2GB'         # 默认任务占用内存
      default-cuda-memory: '2GB'    # 默认任务占用显存
      auto-adjust: false            # 是否自动调整任务占用内存和显存
                                    # 如果同任务组的任务都相同，则可以开启此项功能，会根据已经运行完的任务动态修改默认占用内存和显存
      max-waiting: 10               # 最大等待训练的任务数量
      max-process: 20               # 最大启动进程数量
      interval: 60                  # 每轮调度间隔时间， 时间越长出现OOM的几率越低，一般不建议超出数据集加载时间
      load-nretry: 3                # load操作最大重试次数
      train-nretry: 3               # train操作最大重试次数

    smtp:   # 邮件相关的参数
      enable: false                     # 是否启动发送邮件功能
      server-host: 'smtp.example.com'   # smtp服务器
      server-port: 25
      user: 'user@smtp.example.com'     # 用户名和密码
      password: '******'
      receiver: 'user@smtp.example.com' # 邮件接收者
      min-interval: 3600 # seconds      # 两次发送同类邮件的最低间隔时间，防止邮件数量过多
      max-numbers: 10                   # 一次执行过程中最大邮件数量

