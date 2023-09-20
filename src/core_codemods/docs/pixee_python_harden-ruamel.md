This codemod hardens any unsafe [`ruamel.yaml.YAML()`](https://yaml.readthedocs.io/en/latest/) calls against attacks that could result from deserializing untrusted data.

The fix uses a safety check that already exists in the `ruamel` module, replacing an unsafe `typ` argument with `typ="safe"`.
The changes from this codemod look like this:

```diff
  from ruamel.yaml import YAML
- serializer = YAML(typ="unsafe")
- serializer = YAML(typ="base")
+ serializer = YAML(typ="safe")
+ serializer = YAML(typ="safe")
```
