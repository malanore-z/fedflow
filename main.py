
import fedflow as ff


if __name__ == '__main__':
    with ff.scope("A"):
        print(ff.scope.scope_name())

        with ff.scope("B"):
            print(ff.scope.scope_name())

            with ff.scope("C"):
                print(ff.scope.scope_name())

        with ff.scope("BB"):
            print(ff.scope.scope_name())

    print(ff.scope.scope_name())
