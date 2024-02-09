The `asyncio` [documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task) explicitly discourages manual instantiation of a `Task` instance and instead recommends calling `create_task`.

Our changes look like the following:
```diff
 import asyncio

- task = asyncio.Task(my_coroutine(), name="my task")
+ task = asyncio.create_task(my_coroutine(), name="my task")
```
