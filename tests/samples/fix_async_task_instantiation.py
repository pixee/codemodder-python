import asyncio

async def my_coroutine():
    await asyncio.sleep(1)
    print("Task completed")

async def main():
    task = asyncio.Task(my_coroutine(), name="my task")
    await task

asyncio.run(main())
