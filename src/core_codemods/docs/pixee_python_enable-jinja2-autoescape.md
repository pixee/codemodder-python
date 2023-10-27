This codemod enables autoescaping of HTML content in `jinja2`. Unfortunately, the jinja2 default behavior is to not autoescape when rendering templates, which makes your applications potentially vulnerable to Cross-Site Scripting (XSS) attacks.

Our codemod checks if you forgot to enable autoescape or if you explicitly disabled it. The change looks as follows:

```diff
  from jinja2 import Environment

- env = Environment()
- env = Environment(autoescape=False, loader=some_loader)
+ env = Environment(autoescape=True)
+ env = Environment(autoescape=True, loader=some_loader)
  ...
```
