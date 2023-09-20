This codemod replaces calls to `urllib3.connectionpool.HTTPConnectionPool` and `urllib3.HTTPConnectionPool` with their secure variant (`HTTPSConnectionPool`).

Programmers should opt to use HTTPS over HTTP for secure encrypted communication whenever possible.

```diff
import urllib3
- urllib3.HTTPConnectionPool("www.example.com","80")
+ urllib3.HTTPSConnectionPool("www.example.com","80")
```
