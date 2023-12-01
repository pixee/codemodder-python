Comparisons against `numpy.nan` always result in `False`. Thus comparing an expression directly against `numpy.nan` is always unintended. The correct way to compare a value for `NaN` is to use the `numpy.isnan` function.

Our changes look something like this:

```diff
import numpy as np

a = np.nan
-if a == np.nan:
+if np.isnan(a):
    pass
```
