This codemod ensures you configure jinja2 to turn on autoescaping of HTML content. Unfortunately, the jinja2
default behavior is to not autoescape when rendering templates, which makes your applications
vulnerable to Cross-Site Scripting (XSS) attacks.

Our codemod currently checks if you forgot to turn autoescape on or if you explicitly disabled it. The change looks as follows:

```diff
  from jinja2 import Environment

- env = Environment()
- env = Environment(autoescape=False, loader=some-loader)
+ env = Environment(autoescape=True)
+ env = Environment(autoescape=True, loader=some-loader)
  ...
```

At this time, this codemod will not detect if `autoescape` is assigned to a callable.
