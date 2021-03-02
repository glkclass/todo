#      _____     _
#    /_  __/_ _/ /__
#     / / _ / _ / _ /
#    /_/___/___/___/


def cmd(**kwargs):
    args = ' '.join(
        [f'{key}={str(val)}, type:{type(val)}' for key, val in kwargs.items()])
    print(args)
