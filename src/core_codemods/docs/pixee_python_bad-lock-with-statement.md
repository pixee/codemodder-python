This codemod separates creating a threading lock instance from calling it as a context manager. Calling `with threading.Lock()` does not have the effect you would expect. The lock is not acquired. Instead, to correctly acquire a lock, create the instance separately, before calling it as a context manager.

The change will apply to any of these `threading` classes: `Lock`, `RLock`, `Condition`, `Semaphore`, and `BoundedSemaphore`.

The change looks like this:

```diff
  import threading
- with threading.Lock():
+ lock = threading.Lock()
+ with lock:
     ...
```
