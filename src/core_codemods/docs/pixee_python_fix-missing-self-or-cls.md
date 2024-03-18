Python instance methods must be defined with `self` as the first argument. Likewise, class methods must have `cls` as the first argument. This codemod will add these arguments when the method/class method has no arguments defined.

Our changes look something like this:

```diff
 class MyClass:
-    def instance_method():
+    def instance_method(self):
         print("instance_method")

     @classmethod
-    def class_method():
+    def class_method(cls):
         print("class_method")
```
