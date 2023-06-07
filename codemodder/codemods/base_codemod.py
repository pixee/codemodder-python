class BaseCodemod:
    # Implementation borrowed from https://stackoverflow.com/a/45250114
    NAME = NotImplemented
    DESCRIPTION = NotImplemented
    CHANGESET = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Generalize this
        if cls.NAME is NotImplemented:
            raise NotImplementedError("You forgot to define class attribute: NAME")
        if cls.DESCRIPTION is NotImplemented:
            raise NotImplementedError(
                "You forgot to define class attribute: DESCRIPTION"
            )

    @classmethod
    def full_name(cls):
        return f"pixee:python/{cls.NAME}"
