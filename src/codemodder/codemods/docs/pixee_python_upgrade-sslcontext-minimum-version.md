This codemod replaces all unsafe and/or deprecated SSL/TLS versions when used
to set the `ssl.SSLContext.minimum_version` attribute. It uses
`ssl.TLSVersion.TLSv1_2` instead, which ensures a safe default minimum TLS
version.

Our change involves modifying the `minimum_version` attribute of
`ssl.SSLContext` instances to use `ssl.TLSVersion.TLSv1_2`.

```diff
  import ssl
  context = ssl.SSLContext(protocol=PROTOCOL_TLS_CLIENT)
- context.minimum_version = ssl.TLSVersion.SSLv3
+ context.minimum_version = ssl.TLSVersion.TLSv1_2
```

There is no functional difference between the unsafe and safe versions, and all modern servers offer TLSv1.2.
