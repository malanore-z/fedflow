组件
===========

Task
-----------

1. 属性

    + ``task_id``

        每个task有一个同任务组内唯一id， 根据配置参数的不同，在不同的任务组可能存在相同id。 ``task_id`` 会被作为task工作目录名，因此不能使用路径不允许的字符。  

    + ``device``

        ``Task`` 有一个 ``device`` 属性，用于指定模型训练使用的显卡， 由Fedflow在运行中动态修改值，在定义 ``Task`` 子类时，直接使用即可。  

        ``device`` 被初始化为 ``None`` ， 在调用 ``train`` 方法前， ``device`` 被赋值为Fedflow为此任务分配的显卡对应设备字符串。

        用户可以使用一个字符串指定任务只能使用某个显卡设备。指定显卡设备只能在构造函数中传入字符串， 构造 ``Task`` 实例不能再修改。


    + ``workdir``

        每个任务有其独立的工作目录， 因此在 ``Task`` 方法中不应该使用根目录的相对目录，可能会产生未知错误。 ``workdir`` 被初始化为 ``None``, 在 ``start`` 方法被调用时，
        ``workdir`` 被赋值为工作目录的绝对路径。

    + ``result``

        ``train`` 方法会返回一个字典， 字典的值被保存在 ``result`` 中， 用于在任务运行完后从中获取结果。  

        因为每个任务在单独的子进程中运行，用户不应当通过设置对象属性的方式保留任务运行结果，此种方法的数据不会被传回主进程。

    + ``status``

        ``status`` 属性记录了任务的当前状态， ``status`` 是 ``TaskStatus`` 枚举类的实例。


2. 方法

    + ``start(self) -> None``

        启动任务子进程。

    + ``start_load(self) -> None``

        开始加载数据集。  

    + ``start_train(self, device: str) -> None``

        开始训练。

    + ``is_alive(self) -> bool``

        任务子进程是否在运行。

    + ``exit(self) -> None``

        退出任务子进程。

    + ``load(self) -> None``

        抽象方法，用户定义 ``Task`` 子类中需要实现此方法。

        在 ``load`` 方法中， 执行数据集加载等任务， 为了防止Fedflow占用过多内存， 用户应该尽可能保证在 ``load`` 方法执行完之后， ``Task`` 所占用内存基本不再增长。

        在 ``load`` 方法中， 因为 ``device`` 属性尚未被正确赋值， 因此不能在此方法中执行需要使用显卡的代码。  

    + ``train(self, device: str) -> dict``

        抽象方法，用户定义 ``Task`` 子类中需要实现此方法。

        在 ``train`` 方法中, 执行模型训练过程， 在此方法被调用前， ``device`` 属性被正确赋值，可以使用 ``device`` 属性指定代码要运行在哪个显卡。   


TaskGroup
-----------

1. 属性

    + ``index``

        任务组执行顺序，由Fedflow决定，用户不应该手动修改此属性。  

    + ``group_name``  

        用户可以使用一个有意义的字符串作为任务组名， 如果未指定， 则使用 ``group-{{index}}`` 作为默认任务组名。  

        ``group_name`` 被作为任务组文件系统路径使用，因此不能使用文件路径不允许的字符。

    + ``device``

        用户可以使用一个字符串指定任务组内所有任务只能使用某个显卡设备。  

        指定显卡设备只能在构造函数中传入字符串， 构造 ``TaskGroup`` 实例不能再修改。

    + ``workdir``

        每个任务组有一个独立的工作空间， 在任务组开始被调度时， ``workdir`` 属性被赋值为工作目录的绝对路径。  

    + ``result``

        任务组内任务执行结果被存在 ``result`` 中， 用于生成任务组运行报告。  

2. 方法

    + ``add_task(self, task: Task) -> None``

        向任务组内添加一个任务。  

    + ``get_task(self, task_id: Union[int, str]) -> Union[Task, None]``  

        根据id从任务组内获取任务。  

    + ``report_finish(self, task_id: Union[int, str], data=None) -> None``

        向任务组报告某个任务运行成功， 并记录运行结果。  

    + ``report_exception(self, task_id: Union[int, str], stage: str, message: str) -> None``

        向任务组报告某个任务运行失败， 并记录异常信息。  

    + ``finished(self) -> bool``

        任务组内所有任务是否都运行结束（包括成功和失败）。  

    + ``retrieve_task(self, status) -> Union[Task, None]``

        从任务组内随机获取一个指定状态的任务。  
  