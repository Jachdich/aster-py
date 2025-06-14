import sys
sys.path.append("..")
import src.asterpy as asterpy
from src.asterpy import ConnectionMode
from test_login import *
from test_log_any import *
from test_permissions import *

# This function uses some absolute hackery to work because I am lazy
# It lists all functions starting with test_ and interprets them as tests to be run
# if the function takes an argument "login" then it will automatically log in the client
# as KingJellyfish before passing it to the test function
# Do not question this
# it makes my life a tiny bit easier
def run_tests():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path to aster server>")
    import subprocess, traceback, time
    import inspect
    p = subprocess.Popen([sys.argv[1], "--scratch-db"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.1)
    if p.poll() is not None:
        print("Server terminated!")
        print(p.stderr.read().decode("utf-8"))
        return
    test_functions = [f for f in globals() if f.startswith("test_")]

    succ = 0
    fail = 0

    for func in test_functions:
        f = globals()[func]
        c = asterpy.Client("KingJellyfish", "lol")
        if "login" in inspect.getargs(f.__code__).args:
            c.add_server("localhost", 2345, connect_mode=ConnectionMode.LOGIN)
        else:
            c.add_server("localhost", 2345, connect_mode=ConnectionMode.NEITHER)
        @c.event
        async def on_ready():
            nonlocal succ
            nonlocal fail
            try:
                print(f"{func} ... ", end="")
                await globals()[func](c)
                print("\x1b[32mok\x1b[0m")
                succ += 1
            except AssertionError:
                print("\x1b[31mfailed\x1b[0m")
                fail += 1
                lines = traceback.format_exc(limit=-2).split("\n")
                if lines[-5].endswith("in assert_eq"):
                    lines[1] = ",".join(lines[1].split(",")[-2:]).strip()
                    exc = "\n".join(lines[1:3] + lines[-2:])
                else:
                    lines[1] = ",".join(lines[1].split(",")[-2:]).strip()
                    exc = "\n".join(lines[3:5] + lines[-2:])
                print(exc)
            except Exception:
                print("\x1b[31mfailed\x1b[0m")
                fail += 1
                print(traceback.format_exc())
            await c.servers[0].disconnect()
        c.run()

    p.terminate()
    print("test result: " + ("ok" if succ == len(test_functions) else "fail") + f". {succ} passed; {fail} failed")

if __name__ == "__main__":
    run_tests()
    
