def log(func):
    def wrapper(*args, **kwargs):
        print_str = ''
        if len(args) == 1:
            if isinstance(args[0], dict) and 'course_id' in args[0]:
                print_str = f'{args[0]["course_id"]} {func.__name__}'
            else:
                print_str = f'{args[0]} {func.__name__}'
        elif len(args) == 2 and isinstance(args[1], dict) and 'studentno' in args[1]:
            print_str = f'{args[1]["studentno"]} {func.__name__}'
        else:
            print_str = func.__name__
        print(print_str + ' is running')
        return func(*args, **kwargs)
    return wrapper
