This codemod replaces the use of all unsafe and/or deprecated SSL/TLS versions
in the `ssl.SSLContext` constructor. It uses `PROTOCOL_TLS_CLIENT` instead,
which ensures a safe default TLS version. It also sets the `protocol` parameter
to `PROTOCOL_TLS_CLIENT` in calls without it, which is now deprecated.

Our change involves modifying the argument to `ssl.SSLContext()` to
use `PROTOCOL_TLS_CLIENT`.

```diff
  import ssl
- context = ssl.SSLContext()  
+ context = ssl.SSLContext(protocol=PROTOCOL_TLS_CLIENT)
- context = ssl.SSLContext(protocol=PROTOCOL_SSLv3)
+ context = ssl.SSLContext(protocol=PROTOCOL_TLS_CLIENT)
```

There is no functional difference between the unsafe and safe versions, and all modern servers offer TLSv1.2.

The use of explicit TLS versions (even safe ones) is deprecated by the `ssl`
module, so it is necessary to choose either `PROTOCOL_TLS_CLIENT` or
`PROTOCOL_TLS_SERVER`. Using `PROTOCOL_TLS_CLIENT` is expected to be the
correct choice for most applications but in some cases it will be necessary to
use `PROTOCOL_TLS_SERVER` instead.
