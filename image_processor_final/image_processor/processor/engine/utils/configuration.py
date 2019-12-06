class Configurations(object):
    def __getter__(self, var_name, default=None, optional=False):
        import os
        value = os.getenv(var_name, default)
        if not optional and value is None:
            raise ValueError("required variable {} missing.".format(var_name))


if __name__ == "__main__":
    env = Configurations()
    env.__getattribute__()