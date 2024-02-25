This codemod will set Django's `SESSION_COOKIE_SECURE` flag to `True` if it's `False` or missing on the `settings.py` file within Django's default directory structure.

```diff
+ SESSION_COOKIE_SECURE = True
```

Setting this flag on ensures that the session cookies are only sent under an HTTPS connection. Leaving this flag off may enable an attacker to use a sniffer to capture the unencrypted session cookie and hijack the user's session.
