import asyncio
import psutil

async def run(cmd):
    print("Running: ", cmd)

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    return proc

async def run_with_timeout(cmd, timeout=20):
    proc = await run(cmd)

    try:
        output = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        stdout, _ = output
        return str(stdout).strip()
    except asyncio.TimeoutError:
        if proc.returncode is None:
            parent = psutil.Process(proc.pid)
            for child in parent.children(): 
                child.terminate()
            # parent.terminate()
            print("Terminating Process '{0}' (timed out)".format(cmd))
        
        
asyncio.run(run_with_timeout("D:\\Github\\stresstester\\furmark\\FurMark.exe /nogui /width=1280 /height=720 /run_mode=0 /disable_catalyst_warning", timeout=5))